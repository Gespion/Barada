import json
import scrapy
import datetime

from barada import settings
from barada.items import BaradaItem
from barada.run.funct import connect_to_mongodb, is_url_duplicate, convert_date

class JobsCollector(scrapy.Spider):
    name = "novojob"
    start_urls = ["https://novojob.com/cote-d-ivoire/offres-d-emploi"]

    # Parsing items method
    def parse(self, response):
        # Collect all urls from the page to parse
        urls = response.css('div.bloc-right > div.row-fluid > a::attr(href)').extract() #all

        data_collection = connect_to_mongodb(settings.MONGO_URI,settings.MONGO_DATABASE)

        for url in urls:
            url = response.urljoin(url) #Check if response is valid before going to next step: valid response code??? ###
            # Check if the url already exist in database before scraping the details.
            result = is_url_duplicate(url, data_collection)
            #result = False
            if result is not True:
                yield scrapy.Request(url=url, callback=self.parse_details)
            else:
                pass

        # Follow pagination link next page
        next_page_url = response.css('div.text-center > a.pagination_next::attr(href)').get()
        
        if next_page_url:
            next_page_url = response.urljoin(next_page_url)
            #yield scrapy.Request(url=next_page_url, callback=self.parse,meta={'proxy': 'https://05.196.255.171:3128'})
            yield scrapy.Request(url=next_page_url, callback=self.parse)

    # Parsing items details method
    def parse_details(self, response):

        # Collect json data from previous response            
        raw_data = response.css('div.span12 > div#content.span8 > script::text')[0].get()
        json_data = json.loads(raw_data)

        # Check wether the job offer is active or not
        try:
            job_expire_date = json_data["validThrough"]
            job_expire_date = datetime.datetime.strptime(job_expire_date, '%Y-%m-%d')
            if job_expire_date < datetime.datetime.today():
                job_active = False
            else:
                job_active = True
        except (IndexError, KeyError):
            job_active = True
        
        # If job is active then we proceed
        if job_active is True:

            item = BaradaItem()

            item['job_site'] = 'novojob.com'

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
                item['job_date'] = json_data["datePosted"]  
                item['job_date'] = datetime.datetime.strptime(item['job_date'], '%Y-%m-%d')
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
                item['job_title'] = json_data["title"] 
                if item['job_title'] is None:
                    item['job_title'] = 'N.C'
                else:
                    item['job_title'] = item['job_title'].strip().title()
            except (IndexError, KeyError):
                item['job_title'] = 'N.C'

            # Handling possible empty Company
            try:
                item['job_company'] = json_data["hiringOrganization"]["name"] 
                
                if item['job_company'] is None or item['job_company'] == 'Entreprise anonyme':
                    item['job_company'] = 'N.C'
                else:
                    item['job_company'] = item['job_company'].strip().upper()
            except (IndexError, KeyError):
                item['job_company'] = 'N.C'

            # Handling possible empty Domain
            try:
                job_domain = json_data["occupationalCategory"] 
                if job_domain is not None:
                    item['job_domain'] = self.domain_converter(job_domain)
                    if item['job_domain'] is None:
                        item['job_domain'] = 'N.C'
                else:
                    item['job_domain'] = 'N.C'
            except (IndexError, KeyError):
                item['job_domain'] = 'N.C'

            # Handling possible empty Experience
            try:
                item['job_experience'] = json_data["experienceRequirements"]
                
                if item['job_experience'] is None:
                    item['job_experience'] = 'N.C'    
                else:
                    item['job_experience'] = item['job_experience'].strip()    
            except (IndexError, KeyError):
                item['job_experience'] = 'N.C'

            # Handling possible empty Level
            try:
                job_level = json_data["educationRequirements"]
                
                if job_level is not None:
                    item['job_level_txt'] = job_level.strip()
                    item['job_level_num'] = self.level_converter(job_level)
                    if item['job_level_num'] is None:
                        item['job_level_num'] = 'N.C'
                else:
                    item['job_level_num'] = "['0', '1', '2', '3', '5']"
                    item['job_level_txt'] = 'N.C'
            except (IndexError, KeyError):
                item['job_level_num'] = "['0', '1', '2', '3', '5']"
                item['job_level_txt'] = 'N.C'

            # Assigning variables
            yield item
        else:
            pass

    # Converting Novojob.com domains to TulossJobs's domains
    def domain_converter(self, args):
        domain_list = []
        switcher = {
            "Administration, Moyens généraux": "Divers",
            "Assistanat, secrétariat": "Sécrétariat, Assistanat de Direction",
            "Autre": "Divers",
            "Chantier, Métiers BTP, Architecture": "BTP, Génie civil, Electricité",
            "Commercial, Technico Commercial, Service Client": "Commercial, Vente",
            "Comptabilité, Finance": "Banque, Finance, Comptabilité",
            "Création, Design": "Design, Infographie, Arts graphiques",
            "Direction générale, Direction d'unité": "Management",
            "Education, Enseignement": "Divers",
            "Hôtellerie, Tourisme, Restauration, Loisirs": "Tourisme, Hôtellerie, Restauration",
            "Informatique, Systèmes d'information, Internet": "Informatique, NTIC, Télécoms",
            "Ingénierie, Etudes, Projet, R&D": "Production, Maintenance, QHSE",
            "Journalisme, Médias, Traduction": "Droit, Juridique",
            "Juridique, Fiscal, Audit, Conseil": "Droit, Juridique",
            "Logistique, Achat, Stock, Transport": "Transit, Transport, Logistique",
            "Maintenance, Entretien": "Production, Maintenance, QHSE",
            "Marketing, Communication": "Marketing, RH, Communication",
            "Métiers Banque et assurances": "Banque, Finance, Comptabilité",
            "Métiers de l'agriculture": "Agronomie",
            "Ouvriers qualifiés, Chauffeur": "Divers",
            "Production, méthode, industrie": "Production, Maintenance, QHSE",
            "Qualité, Sécurité, Environnement": "Production, Maintenance, QHSE",
            "Responsable Commercial, Grands comptes": "Commercial, Vente",
            "RH, personnel, formation": "Marketing, RH, Communication",
            "Santé, Médical, Pharmacie": "Santé, Sciences sociales",
            "Télécommunication, Réseaux": "Informatique, NTIC, Télécoms",
            "Vente, Télévente, Assistanat": "Commercial, Vente",
        }

        # Loop to get domain conversion from the dictionary switcher
        args = args.split("|") # Transformation en liste
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
                'formation professionnelle': '1',
                'baccalauréat': '1',
                'universitaire sans diplôme': '1',
                'ts bac +2': '2',
                'licence (lmd), bac + 3': '3',
                'master 1, licence  bac + 4': '4',
                'master 2, ingéniorat, bac + 5': '5',
                'magistère bac + 7': '5',
                'doctorat': '5',
            }   # Vu les potentiels soucis d'espace, on pourrait plus tard strip tous les espaces avant de comparer

            #  Loop to get domain conversion from the dictionary switcher
            args = args.split("|") # Transformation en liste
            for arg in args:
                arg = arg.strip().lower()  # Remove useless spaces before and after the level
                # print("Arg: ",arg)
                clean_arg = switcher.get(arg, '0') # Call to switch level method, 0 is default
                if clean_arg not in level_list:  # Check to avoid duplicate in final level list
                    level_list.append(clean_arg)  # If not already in the list then add
            # print("List item: " + str(level_list))

            return str(level_list)
