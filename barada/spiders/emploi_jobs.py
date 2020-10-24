import json
import scrapy
import datetime

from barada import settings
from barada.items import BaradaItem
from barada.run.funct import connect_to_mongodb, is_url_duplicate, convert_date

class JobsCollector(scrapy.Spider):
    name = "emploi"
    start_urls = ["https://www.emploi.ci/recherche-jobs-cote-ivoire"]

    # Parsing items method
    def parse(self, response):
        # Collect all urls from the page to parse
        urls = response.css('div.col-lg-5 > h5 > a::attr(href)').extract()

        data_collection = connect_to_mongodb(settings.MONGO_URI,settings.MONGO_DATABASE)

        for url in urls:
            url = response.urljoin(url) #Check if response is valid before going to next step: valid response code??? ###
            # Check if the url already exist in database before scraping the details.
            result = is_url_duplicate(url, data_collection)
            if result is not True:
                yield scrapy.Request(url=url, callback=self.parse_details)
            else:
                pass

        # Follow pagination link next page
        next_page_url = response.css('li.pager-next.active.last > a::attr(href)').extract_first()
        if next_page_url:
            next_page_url = response.urljoin(next_page_url)
            yield scrapy.Request(url=next_page_url, callback=self.parse)

    # Parsing items details method
    def parse_details(self, response):

        raw_data = response.css('div#content.region-content.nested.grid16-16 > div#content-inner.content-inner.inner > script::text')[0].get()
        raw_data = raw_data.replace('\n', ' ').replace('\r', '')
        json_data = json.loads(raw_data)

        # Check wether the job offer is active or not
        try:
            job_expire_date = json_data["validThrough"][0:10]
            job_expire_date = datetime.datetime.strptime(job_expire_date, '%Y-%m-%d')
            #print(job_expire_date)
            if job_expire_date < datetime.datetime.today():
                job_active = False
                #print("Emploi expiré")
            else:
                job_active = True
                #print("Emploi valide")
        except (IndexError, KeyError):
            job_active = True
        
        # If job is active then we proceed
        if job_active is True:
            item = BaradaItem()

            item['job_site'] = 'emploi.ci'

            item['job_scrape_date'] = datetime.datetime.today()

            # Handling possible empty URL
            try:
                item['job_url'] = response.urljoin(response.url)
                if item['job_url'] is None:
                    item['job_url'] = 'N.C'
            except (IndexError, KeyError):
                item['job_url'] = 'N.C'

            # Handling possible empty Date
            try:
                item['job_date'] = response.css('div.job-ad-publication-date::text').get()
                item['job_date'] = convert_date(item['job_site'], item['job_date'])
                if item['job_date'] is None:
                    item['job_date'] = datetime.datetime.today()
            except (IndexError, KeyError):
                item['job_date'] = datetime.datetime.today()

            # Handling possible empty Expiration Date
            try:
                item['job_expire_date'] = job_expire_date
                if item['job_expire_date'] is None:
                    item['job_expire_date'] = datetime.datetime.today() # How to properly handle empty expiration dates?
            except (IndexError, KeyError):
                item['job_expire_date'] = datetime.datetime.today() # How to properly handle empty expiration dates?

            # Handling possible empty Title
            try:
                item['job_title'] = response.css('h1.title::text').get()
                if item['job_title'] is None:
                    item['job_title'] = 'N.C'
                else:
                    item['job_title'] = item['job_title'].strip().title()
            except (IndexError, KeyError):
                item['job_title'] = 'N.C'

            # Handling possible empty Company
            try:
                item['job_company'] = response.css('div.company-title > a::text').get()
                
                if item['job_company'] is None:
                    item['job_company'] = 'N.C'
                else:
                    item['job_company'] = item['job_company'].strip().upper()
            except (IndexError, KeyError):
                item['job_company'] = 'N.C'

            # Handling possible empty Domain
            try:
                job_domain = response.css('div.field.field-name-field-offre-metiers.field-type-taxonomy-term-reference.field-label-hidden > div.field-items > div.field-item::text').getall()
                #job_domain = job_domain.split(",") #Vient déja en liste... A vérifier
                item['job_domain'] = self.domain_converter(job_domain)
                if item['job_domain'] is None:
                    item['job_domain'] = 'N.C'
            except (IndexError, KeyError):
                item['job_domain'] = 'N.C'

            # Handling possible empty Experience
            try:
                item['job_experience'] = response.css('div.field.field-name-field-offre-niveau-experience.field-type-taxonomy-term-reference.field-label-hidden > div.field-items > div.field-item::text').get()       
                
                if item['job_experience'] is None:
                    item['job_experience'] = 'N.C'    
                else:
                    item['job_experience'] = item['job_experience'].strip()    
            except (IndexError, KeyError):
                item['job_experience'] = 'N.C'

            # Handling possible empty Level
            try:
                job_level = response.css('div.field.field-name-field-offre-niveau-etude.field-type-taxonomy-term-reference.field-label-hidden > div.field-items > div.field-item::text').get()
                item['job_level_txt'] = job_level.strip()
                item['job_level_num'] = self.level_converter(job_level)
                if item['job_level_num'] is None:
                    item['job_level_num'] = "['0', '1', '2', '3', '5']"
            except (IndexError, KeyError):
                item['job_level_num'] = "['0', '1', '2', '3', '5']"
                item['job_level_txt'] = 'N.C'

            # Assigning variables
            yield item
        else:
            pass

    # Converting Emploi.ci domains to TulossJobs's domains
    def domain_converter(self, args):
        domain_list = []
        switcher = {
            "Achats": "Commercial, Vente",
            "Commercial, vente": "Commercial, Vente",
            "Gestion, comptabilité, finance": "Banque, Finance, Comptabilité",
            "Informatique, nouvelles technologies": "Informatique, NTIC, Télécoms",
            "Juridique": "Droit, Juridique",
            "Management, direction générale": "Management",
            "Marketing, communication": "Marketing, RH, Communication",
            "Métiers de la santé et du social": "Santé, Sciences sociales",
            "Métiers des services": "Divers",
            "Métiers du BTP": "BTP, Génie civil, Electricité",
            "Production, maintenance, qualité": "Production, Maintenance, QHSE",
            "R&D, gestion de projets": "Management",
            "RH, formation": "Marketing, RH, Communication",
            "Secretariat, assistanat": "Sécrétariat, Assistanat de Direction",
            "Tourisme, hôtellerie, restauration": "Tourisme, Hôtellerie, Restauration",
            "Transport, logistique": "Transit, Transport, Logistique",
        }

        # Loop to get domain conversion from the dictionary switcher
        for arg in args:
            arg = arg.strip() # Remove useless spaces before and after the domain
            clean_arg = switcher.get(arg, "Divers") # Call to switch domain method
            if clean_arg not in domain_list: # Check to avoid duplicate in final domain list
                domain_list.append(clean_arg) # If not already in the list then add

        return domain_list

    # Converting levels to Tuloss Jobs's levels
    def level_converter(self, args):
            level_list = []
            switcher = {
                'bac': '1',
                'bac+1': '1',
                'bac+2': '2',
                'bac+3': '3',
                'bac+4': '4',
                'bac+5': '5',
                'bac+5 et plus': '5',
                'bac+6': '5',
                'bac+7 et plus': '5',
            }

            #  Loop to get domain conversion from the dictionary switcher
            args = args.split(",") # Transformation en liste
            for arg in args:
                arg = arg.strip().lower()  # Remove useless spaces before and after the level
                # print("Arg: " + arg)
                clean_arg = switcher.get(arg, '0') # Call to switch level method, 0 is default
                if clean_arg not in level_list:  # Check to avoid duplicate in final level list
                    level_list.append(clean_arg)  # If not already in the list then add
            # print("List item: " + str(level_list))

            return str(level_list)
