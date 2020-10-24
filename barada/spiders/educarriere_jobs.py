import scrapy
import datetime

from barada import settings
from barada.items import BaradaItem
from barada.run.funct import connect_to_mongodb, is_url_duplicate, convert_date

class JobsCollector(scrapy.Spider):
    name = "educarriere"
    start_urls = ["http://emploi.educarriere.ci/nos-offres?page1=0"]

    # Parsing items method
    def parse(self, response):
        # Collect all urls from the page to parse
        urls = response.css('div.box.row > div.text-col.post.small-post.col-md-8.col-xs-12 > h4 > a::attr(href)').getall()

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
        next_page_url = response.css('tr > td > a::attr(href)')[1].get()
        if next_page_url:
            next_page_url = response.urljoin(next_page_url)
            yield scrapy.Request(url=next_page_url, callback=self.parse)

    # Parsing items details method
    def parse_details(self, response):

        # Check wether the job offer is active or not
        try:
            job_expire_date = response.css('li.list-group-item > span::text')[1].get()
            job_expire_date = datetime.datetime.strptime(job_expire_date, '%d/%m/%Y')
            if job_expire_date < datetime.datetime.today():
                job_active = False
            else:
                job_active = True    
        except (IndexError, KeyError):
            job_active = True

        if job_active is True:

            item = BaradaItem()

            item['job_site'] = 'educarriere.ci'

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
                item['job_date'] = response.css('li.list-group-item > span::text')[0].get()
                item['job_date'] = convert_date(item['job_site'], item['job_date'])
                if item['job_date'] is None:
                    item['job_date'] = datetime.datetime.today()
            except (IndexError, KeyError):
                item['job_date'] = datetime.datetime.today()

            # Handling possible empty Expiration Date
            try:
                item['job_expire_date'] = job_expire_date  
                #item['job_expire_date'] = convert_date(item['job_site'], item['job_expire_date'])
                if item['job_expire_date'] is None:
                    item['job_expire_date'] = datetime.datetime.today() # How to properly handle empty expiration dates?
            except (IndexError, KeyError):
                item['job_expire_date'] = datetime.datetime.today() # How to properly handle empty expiration dates?

            # Handling possible empty Title
            try:
                item['job_title'] = response.css('ul.list-group > li.list-group-item::text')[4].get()
                if item['job_title'] is None:
                    item['job_title'] = 'N.C'
                else:
                    item['job_title'] = item['job_title'].strip().title()
            except (IndexError, KeyError):
                item['job_title'] = 'N.C'

            # Handling possible empty Company
            try:
                item['job_company'] = response.css('div.post-content > div.entry-content > p > strong::text')[0].get()

                if item['job_company'] is None:
                    item['job_company'] = 'N.C'
                else:
                    item['job_company'] = item['job_company'].strip().upper()
            except (IndexError, KeyError): 
                item['job_company'] = 'N.C'

            # Handling possible empty Domain
            try:
                job_domain = response.css('ul.list-group > li.list-group-item::text')[6].get()
                job_domain = job_domain.split(",")
                item['job_domain'] = self.domain_converter(job_domain)
                if item['job_domain'] is None:
                    item['job_domain'] = 'N.C'
            except (IndexError, KeyError):
                item['job_domain'] = 'N.C'

            # Handling possible empty Experience
            try:
                item['job_experience'] = response.css('ul.list-group > li.list-group-item::text')[8].get().strip()
                if item['job_experience'] is None:
                    item['job_experience'] = 'N.C'
            except (IndexError, KeyError):
                item['job_experience'] = 'N.C'

            # Handling possible empty Level
            try:
                job_level = response.css('ul.list-group > li.list-group-item::text')[7].get()
                item['job_level_txt'] = job_level.strip()
                item['job_level_num'] = self.level_converter(job_level)
                if item['job_level_num'] is None:
                    item['job_level_num'] = "['0', '1', '2', '3', '5']"
            except (IndexError, KeyError):
                item['job_level_num'] = "['0', '1', '2', '3', '5']"
                item['job_level_txt'] = 'N.C'

            # Assigning variables
            yield item

    # Converting Educarriere.ci domains to TulossJobs's domains
    def domain_converter(self, args):
        domain_list = []
        switcher = {
            "Actuariat": "Divers",
            "Aéronautique": "Divers",
            "Agriculture": "Agronomie",
            "Agroéconomie": "Agronomie",
            "Agronomie": "Agronomie",
            "Aide soignant": "Santé, Sciences sociales",
            "Aménagement du Territoire": "BTP, Génie civil, Electricité",
            "Anthropologie": "Santé, Sciences sociales",
            "Aquaculture": "Agronomie",
            "Architecture": "Divers",
            "Archivistique": "Informatique, NTIC, Télécoms",
            "Assistanat de Direction": "Sécrétariat, Assistanat de Direction",
            "Assurance": "Banque, Finance, Comptabilité",
            "Auxiliaire en pharmacie": "Santé, Sciences sociales",
            "Banque": "Banque, Finance, Comptabilité",
            "Bâtiment": "BTP, Génie civil, Electricité",
            "Biochimie": "Santé, Sciences sociales",
            "Biologie": "Santé, Sciences sociales",
            "Biomédical": "Santé, Sciences sociales",
            "Blanchisserie": "Divers",
            "Boucherie": "Tourisme, Hôtellerie, Restauration",
            "Boulangerie": "Tourisme, Hôtellerie, Restauration",
            "Caisse": "Divers",
            "Calligraphie/Sérigraphie": "Design, Infographie, Arts graphiques",
            "Cariste": "Divers",
            "Carrelage": "BTP, Génie civil, Electricité",
            "Cartographie": "BTP, Génie civil, Electricité",
            "Chaudronnerie": "BTP, Génie civil, Electricité",
            "Chimie": "Santé, Sciences sociales",
            "Coiffure": "Divers",
            "Collectivités Territoriales": "Santé, Sciences sociales",
            "Commerce et Administration des Entreprises": "Management",
            "Commerce/Ventes": "Commercial, Vente",
            "Communication": "Marketing, RH, Communication",
            "Construction Metallique": "BTP, Génie civil, Electricité",
            "Contrôle de gestion/Audit": "Banque, Finance, Comptabilité",
            "Contrôle Industriel et Régulation Automatique": "Production, Maintenance, QHSE",
            "Cosmétologie": "Divers",
            "Couture/Broderie": "Divers",
            "Criminologie": "Droit, Juridique",
            "Délégation médicale": "Santé, Sciences sociales",
            "Documentation": "Informatique, NTIC, Télécoms",
            "Econométrie": "Banque, Finance, Comptabilité",
            "Economie": "Banque, Finance, Comptabilité",
            "Education/Enseignement": "Marketing, RH, Communication",
            "Electrobiomédical": "Santé, Sciences sociales",
            "Electrobobinage": "Production, Maintenance, QHSE",
            "Electromécanique": "Production, Maintenance, QHSE",
            "Electronique": "Production, Maintenance, QHSE",
            "Electrotechnique/Electricité": "BTP, Génie civil, Electricité",
            "Elevage": "Agronomie",
            "Energétique": "Production, Maintenance, QHSE",
            "Entretien/Nettoyage": "Divers",
            "Environnement": "Divers",
            "Esthétique/Beauté": "Divers",
            "Ferraillage": "Production, Maintenance, QHSE",
            "Ferronnerie": "Production, Maintenance, QHSE",
            "Finances/Comptabilité": "Banque, Finance, Comptabilité",
            "Fiscalité": "Banque, Finance, Comptabilité",
            "Foresterie": "Agronomie",
            "Froid": "BTP, Génie civil, Electricité",
            "Généraliste": "Divers",
            "Génie Civil/Travaux publics": "BTP, Génie civil, Electricité",
            "Génie Mécanique et Productique": "Production, Maintenance, QHSE",
            "Géomètre/Topographe": "BTP, Génie civil, Electricité",
            "Gestion": "Management",
            "Gestion des PME-PMI": "Management",
            "Hôtellerie/Restauration": "Tourisme, Hôtellerie, Restauration",
            "Hydraulique": "Production, Maintenance, QHSE",
            "Hygiène Industrielle": "Production, Maintenance, QHSE",
            "Immobilier": "BTP, Génie civil, Electricité",
            "Imprimerie": "Design, Infographie, Arts graphiques",
            "Incendie Prévention": "Production, Maintenance, QHSE",
            "Industrie Agro-alimentaire" : "Agronomie",
            "Infographie": "Design, Infographie, Arts graphiques",
            "Informatique": "Informatique, NTIC, Télécoms",
            "Informatique de Gestion": "Informatique, NTIC, Télécoms",
            "Journalisme": "Marketing, RH, Communication",
            "Juridique/Droit": "Droit, Juridique",
            "Logistique/Transport": "Transit, Transport, Logistique",
            "Magasinage": "Transit, Transport, Logistique",
            "Maintenance des Systèmes de Production": "Production, Maintenance, QHSE",
            "Maintenance Informatique": "Informatique, NTIC, Télécoms",
            "Maintenance véhicules et engins": "Production, Maintenance, QHSE",
            "Management": "Management",
            "Marketing": "Marketing, RH, Communication",
            "Mathématique Financière": "Banque, Finance, Comptabilité",
            "Mécanique": "Production, Maintenance, QHSE",
            "Mécanique et Automatisme Industriel": "Production, Maintenance, QHSE",
            "Médecine/Santé": "Santé, Sciences sociales",
            "Menuiserie": "BTP, Génie civil, Electricité",
            "Météorologie": "Divers",
            "Mines/Géologie/Pétrole": "Mines, Géologie, Pétrole",
            "Moteurs et Equipements Motorisés": "Production, Maintenance, QHSE",
            "Musique": "Divers",
            "NTIC": "Informatique, NTIC, Télécoms",
            "Optique/Lunetterie": "Santé, Sciences sociales",
            "Pêche": "Agronomie",
            "Peinture": "Divers",
            "Pharmacie": "Santé, Sciences sociales",
            "Philosophie": "Santé, Sciences sociales",
            "Photographie": "Design, Infographie, Arts graphiques",
            "Phytosanitaire": "Agronomie",
            "Plomberie": "BTP, Génie civil, Electricité",
            "Psychologie": "Santé, Sciences sociales",
            "Qualité": "Production, Maintenance, QHSE",
            "Ressources Animales et Halieutiques": "Agronomie",
            "Ressources Humaines": "Marketing, RH, Communication",
            "Sciences halieutes": "Agronomie",
            "Sciences politiques": "Santé, Sciences sociales",
            "Sciences sociales": "Santé, Sciences sociales",
            "Secrétariat": "Sécrétariat, Assistanat de Direction",
            "Sécurité/Défense": "Production, Maintenance, QHSE",
            "Sociologie": "Santé, Sciences sociales",
            "Soudure": "BTP, Génie civil, Electricité",
            "Sports": "Divers",
            "Statistiques": "Banque, Finance, Comptabilité",
            "Tapisserie": "Divers",
            "Télécommunications": "Informatique, NTIC, Télécoms",
            "Thermodynamique": "Production, Maintenance, QHSE",
            "Topographie": "BTP, Génie civil, Electricité",
            "Tourisme/Loisirs": "Tourisme, Hôtellerie, Restauration",
            "Traduction/Interprétariat": "Marketing, RH, Communication",
            "Transit/Transport": "Transit, Transport, Logistique",
            "Transport (Chauffeur)": "Transit, Transport, Logistique",
            "Urbanisme": "BTP, Génie civil, Electricité",
            "Vitrerie": "BTP, Génie civil, Electricité",
            "Zootechnie": "Agronomie",
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
