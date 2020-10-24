import json
# Collect json data from previous response            
#raw_data = response.css('div.span12 > div#content.span8 > script::text')[0].get() ###novojob
raw_data = response.css('div#content.region-content.nested.grid16-16 > div#content-inner.content-inner.inner > script::text')[0].get() ###emploi.ci
raw_data = raw_data.replace('\n', ' ').replace('\r', '')
json_data = json.loads(raw_data)

# Handling possible empty Date
print(json_data["datePosted"])

# Handling possible empty ValidThrough
print(json_data["validThrough"])

# Handling possible empty Title
print(json_data["title"])

# Handling possible empty Company
print(json_data["hiringOrganization"]["name"])

# Handling possible empty Domain
print(json_data["occupationalCategory"])

# Handling possible empty Experience
print(json_data["experienceRequirements"])

# Handling possible empty Level
print(json_data["educationRequirements"])

----
A tester sur emploi.ci
https://www.emploi.ci/offre-emploi-cote-ivoire/conseiller-diplomatie-humanitaire-partenariat-820454
https://www.emploi.ci/offre-emploi-cote-ivoire/developpeur-php-laravel-abidjan-830288

novojob
- offres d'emploi sans level défini