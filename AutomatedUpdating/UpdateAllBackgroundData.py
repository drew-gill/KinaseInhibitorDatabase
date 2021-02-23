import requests
import csv
from zipfile import ZipFile
from io import BytesIO
import mysql.connector
#from openbabel import openbabel
import os
import subprocess

#might work with 3.1.1, but 2.4.0 (or older) was the only one that worked with generating3D coordinates
openbabelExecutablePath = "C:\Program Files\OpenBabel-2.4.0\obabel"
tempDataPath = "TEMP_DATA/"

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="kinasedb",
  database="research"
)

#The ordering of traits does not seem to be consistent month-to-month for PKIDB updated database of drugs
#Examine SDF file and update the index values below as necessary
pkidbSDFOrdering = {
    "name": 0,
    "phase": 7, #phase
    "company": 2, #applicants
    "smiles": 4, #canonical_smiles
    "inchi": 15, #stdInchiKey
    "description": 22, #AKA indications
    "aliases1": 1, #brand name
    "aliases2": 9, #other aliases
    "dbLinks": 17, #database links, e.g. chemspider.com
    "targets": 32 #kinase targets, e.g. ABL1
}

def combineURLandSplit(startIndex, splitInfo):
    stringOut = splitInfo[startIndex]

    iShift = 1
    while('|' in splitInfo[startIndex + iShift]):
        stringOut += splitInfo[startIndex+iShift]
        iShift += 1
    
    urlArray = stringOut.split('|')

    for item in urlArray:
        if(item == None or item == ""):
            urlArray.remove(item)

    return urlArray

def getLastIndex(string, target):
    return string.find(target) + len(target)

def getKnownInhibitors():
    baseURL = "https://www.icoa.fr/pkidb/"

    r = requests.get(baseURL)

    contentText = r.text
    downloadLocationStart = contentText.find("static/download/")
    downloadLocationEnd = contentText.find("'", downloadLocationStart)
    appendText = contentText[downloadLocationStart:downloadLocationEnd]

    downloadURL = baseURL + appendText

    pkidbFile = requests.get(downloadURL, allow_redirects=True)

    pkidbText = pkidbFile.text
    splitByLine = pkidbText.split('\n')

    inhibitorsAndInfo = [[splitByLine[0]]]

    currentInhibitorIndex = 0

    for i,item in enumerate(splitByLine):
        if(i == 0):
            continue
        if('>  <' in splitByLine[i-1]):
            if('|' in item):
                item = combineURLandSplit(i, splitByLine)
            elif(item == 'nan'):
                item = None
            inhibitorsAndInfo[currentInhibitorIndex].append(item)
        if('$$$$' in splitByLine[i-1]):
            if(item != ''):
                inhibitorsAndInfo.append([item])
            currentInhibitorIndex += 1

    #important values from this file:
    #NAME, Alias, Company, DRUGBANK, targets, description, pubchem, chemspider, FDA approval, synonyms (more aliases), smiles, inchi

    outputDictionaries = []

    for i,item in enumerate(inhibitorsAndInfo):
        inhibitorDictionary = {
            "name": inhibitorsAndInfo[i][pkidbSDFOrdering["name"]],
            "aliases": None, #separate, append stripped aliases in [23]
            "phase": int(inhibitorsAndInfo[i][pkidbSDFOrdering["phase"]][0]),
            "company": inhibitorsAndInfo[i][pkidbSDFOrdering["company"]],
            "drugbankID": None, #separate
            "pubchemCompound": None, #separate
            "chemspider": None, #separate
            "smiles": inhibitorsAndInfo[i][pkidbSDFOrdering["smiles"]],
            "inchi": inhibitorsAndInfo[i][pkidbSDFOrdering["inchi"]],
            "targets": None, #separate
            "description": inhibitorsAndInfo[i][pkidbSDFOrdering["description"]],
            "chembl": None #separate
        }

        #GET ALIASES
        possibleAliases = inhibitorsAndInfo[i][pkidbSDFOrdering["aliases1"]]

        if(possibleAliases != None and possibleAliases.strip() != ""):
            inhibitorDictionary["aliases"] = inhibitorsAndInfo[i][pkidbSDFOrdering["aliases1"]].split(";")
        else:
            inhibitorDictionary["aliases"] = []
        
        possibleAliases = inhibitorsAndInfo[i][pkidbSDFOrdering["aliases2"]]

        if(isinstance(possibleAliases, list)):
            for item in inhibitorsAndInfo[i][pkidbSDFOrdering["aliases2"]]:
                inhibitorDictionary["aliases"].append(item.strip())
        elif(possibleAliases != ""):
            inhibitorDictionary["aliases"].append(possibleAliases.strip())
        
        #GET IDs
        for item in inhibitorsAndInfo[i][pkidbSDFOrdering["dbLinks"]]:
            if('chemspider' in item):
                idIndexStart = getLastIndex(item, "Chemical-Structure.") #starting index of the id
                idIndexEnd = item.find(".html") #ending index of id
                inhibitorDictionary["chemspider"] = item[idIndexStart:idIndexEnd]
                continue

            if('pubchem' in item):
                if('/compound/' in item):
                    idIndexStart = getLastIndex(item, '/compound/')
                    inhibitorDictionary["pubchemCompound"] = item[idIndexStart:]
                else:
                    print("Substance?")
                continue
                

            if('drugbank' in item):
                idIndexStart = getLastIndex(item, '/drugs/')
                inhibitorDictionary["drugbankID"] = item[idIndexStart:]
                continue

            if('/chembldb/compound/inspect/' in item):
                idIndexStart = getLastIndex(item, '/chembldb/compound/inspect/')
                inhibitorDictionary["chembl"] = item[idIndexStart:]
                continue

        #GET TARGETS
        if(inhibitorsAndInfo[i][pkidbSDFOrdering["targets"]] != None):
            inhibitorDictionary["targets"] = inhibitorsAndInfo[i][pkidbSDFOrdering["targets"]].split("; ")        

        outputDictionaries.append(inhibitorDictionary)
    
    return outputDictionaries

def GetLatestDrugbankIdentifiers():
    latestDrugbankDataURL = "https://drugbank.ca/releases/latest/downloads/all-drugbank-vocabulary"

    r = requests.get(latestDrugbankDataURL, allow_redirects=True)

    in_memory = BytesIO(r.content)
    zf = ZipFile(in_memory, "a")
    vocabFile = zf.open("drugbank vocabulary.csv")
    results = vocabFile.read().decode()
    results = results.split('\n')
    results.remove(results[0])

    for i, item in enumerate(results):
        if(item == ''):
            results.remove(item)
            continue
        item = item.split(',')
        item.remove(item[1]) #remove Accession number
        item.remove(item[2]) #remove CAS
        item.remove(item[2]) #remove UNII
        item.remove(item[3]) #remove INCHI

        for j, subItem in enumerate(item):
            if(subItem == '""' or subItem == ""): #make empty slots into None objects
                subItem = None
            elif(' | ' in subItem): #split all aliases into array
                subItem = subItem.split(' | ')
            elif(j == 2): #even if there is only one other alias, make it into an array
                subItem = [subItem]
            item[j] = subItem
        
        if(item[2] != None):
            item[2].append(item[1]) #make a single array of all known aliases, including common name
        else:
            item[2] = [item[1]]
        item.remove(item[1]) #remove the common name entry

        results[i] = item

    #convert array into dictionary where keys == aliases, values == DrugbankID
    aliasToIDDict = {}
    idToAliasesDict = {}
    for listing in results:
        idToAliasesDict[listing[0]] = []
        for alias in listing[1]:
            aliasToIDDict[alias] = listing[0]
            idToAliasesDict[listing[0]].append(alias)
    return (aliasToIDDict, idToAliasesDict)


def JoinDrugbankData(knownInhibitorDictionaries):
    (latestDrugbankData, idToAliasDict) = GetLatestDrugbankIdentifiers()

    #using known names and aliases of kinase inhibitors, look for drugbankIDs
    for index, knownInhibitor in enumerate(knownInhibitorDictionaries):
        if(knownInhibitor["name"] in latestDrugbankData):
            knownInhibitor["drugbankID"] = latestDrugbankData[knownInhibitor["name"]]
        elif(knownInhibitor["aliases"] != None):
            for alias in knownInhibitor["aliases"]:
                if(alias in latestDrugbankData):
                    knownInhibitor["drugbankID"] = latestDrugbankData[alias]

    #add other known names of the inhibitors from drugbank, if available.
    for index, knownInhibitor in enumerate(knownInhibitorDictionaries):
        if(knownInhibitor["drugbankID"] != None):
            if(knownInhibitor["drugbankID"] in idToAliasDict):
                for alias in idToAliasDict[knownInhibitor["drugbankID"]]:
                    if(alias != knownInhibitor["name"]):
                        if(knownInhibitor["aliases"] == None):
                            knownInhibitor["aliases"] = [alias]
                        elif(alias not in knownInhibitor["aliases"]):
                            knownInhibitor["aliases"].append(alias)
                knownInhibitorDictionaries[index] = knownInhibitor
        

    return knownInhibitorDictionaries

def GetSpecificDrugbankData(inhibitorData):
    for drug in inhibitorData:
        if(drug["drugbankID"] != None):
            getURL = "https://drugbank.ca/drugs/%s" % drug["drugbankID"]
            req = requests.get(getURL)

            drugbankText = req.text
            
            potentialNewTargets = []
            while(drugbankText.find('/uniprot/') != -1): #get all linked protein targets of the drugbank entry.
                startIndex = getLastIndex(drugbankText, '/uniprot/')
                drugbankText = drugbankText[startIndex:]
                targetUniprot = drugbankText[:drugbankText.find('"')]

                if(drug["targets"] == None):
                    drug["targets"] = [targetUniprot]
                elif(targetUniprot not in drug["targets"]): #even though this check is done, this is getting the uniprotID, whereas PKIDB provided names. Will need to cross-check in later step
                    drug["targets"].append(targetUniprot) 

            drug["targets"] = RemoveDuplicateNonKinaseUniprots(drug["targets"])
            UpdateInhibitorInDB(drug) #update mySQL db with new data from queries

            if(drug["drugbankID"] != None):
                FindConvertUploadStructure(drug["drugbankID"])

    return inhibitorData

#obabel 3.1 does not work for some reason. Use obabel 2.4
def FindConvertUploadStructure(drugbankID):
    cursor = mydb.cursor()

    getURL = "https://www.drugbank.ca/structures/small_molecule_drugs/%s.sdf" % drugbankID
    getFile = requests.get(getURL, allow_redirects=True)
    newFileName = "%s.pdb" % drugbankID

    tempInputFile = tempDataPath + "TEMPORARY_FILE.sdf"
    tempOutputFile = tempDataPath + newFileName

    with open(tempInputFile, mode="w", encoding="utf-8") as sdf:
        sdf.write(getFile.text)
    
    print(drugbankID)
    
    #"C:\Program Files\OpenBabel-2.4.0\obabel" test/DB15247.sdf -O test/DB15247test2.pdb -d --gen3d
    command = ('"%s" %s -O %s -d --gen3d') % (openbabelExecutablePath, tempInputFile, tempOutputFile)

    subprocess.call(command)

    with open(tempOutputFile, mode="rb") as binFile:
        binaryFile = binFile.read()

    insertVals = (binaryFile, drugbankID, newFileName) #binary format of converted PDB file, with 3D coordinates and Hydrogens removed 
    databaseQuery = "SELECT structurefilename FROM structuralfiles WHERE drugbank_id = %s AND structurefilename = %s"
    cursor.execute(databaseQuery, [drugbankID, newFileName])

    outputID = cursor.fetchone()
    if(outputID != None and len(outputID) >= 1):
        databaseQuery = "UPDATE structuralfiles SET structure = %s WHERE drugbank_id = %s AND structurefilename = %s"
    else:
        databaseQuery = "INSERT INTO structuralfiles (structure, drugbank_id, structurefilename) VALUES (%s, %s, %s)"

    cursor.execute(databaseQuery, insertVals)
    mydb.commit()

    cursor.close()

    os.remove(tempOutputFile)


def RemoveDuplicateNonKinaseUniprots(uniprotTargets):
    if(uniprotTargets == None or len(uniprotTargets) == 0):
        return uniprotTargets

    cursor = mydb.cursor()
    databaseQuery = "SELECT uniprot_id FROM kinaseproteins WHERE uniprot_id = %s OR HGNC_Name = %s OR Manning_Name = %s OR Descriptive_Name = %s OR x_Name = %s"
    uniprotTargetIDs = []
    
    for target in uniprotTargets:
        cursor.execute(databaseQuery, (target, target, target, target, target))
        outputID = cursor.fetchone() #check if "target" is a kinase
        if(outputID != None and len(outputID) == 1):
            outputID = outputID[0]
        else:
            uniprotTargets.remove(target)

        if(outputID in uniprotTargetIDs): #remove duplicates
            uniprotTargets.remove(target)
        else:
            uniprotTargetIDs.append(target)

    cursor.close()
    return uniprotTargetIDs

def UpdateInhibitorInDB(inhibitorData):
    cursor = mydb.cursor()
    databaseQuery = "SELECT name FROM kinasedrugs WHERE drugbank_id = %s OR name = %s"
    
    #UPDATE THE KINASEDRUGS TABLE
    cursor.execute(databaseQuery, (inhibitorData["drugbankID"], inhibitorData["name"]))
    outputName = cursor.fetchone() #check if inhibitor is already in db
    if(outputName != None and len(outputName) == 1):
        databaseQuery = "UPDATE kinasedrugs SET phase = %s, chembl = %s, company = %s, drugbank_id = %s, pubchem_compound = %s, chemspider = %s, smiles = %s, inchi_key = %s, description = %s WHERE name = %s"
    else:
        databaseQuery = "INSERT INTO kinasedrugs (phase, chembl, company, drugbank_id, pubchem_compound, chemspider, smiles, inchi_key, description, name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    
    cursor.execute(databaseQuery, (inhibitorData["phase"], inhibitorData["chembl"], inhibitorData["company"], inhibitorData["drugbankID"], inhibitorData["pubchemCompound"], inhibitorData["chemspider"], inhibitorData["smiles"], inhibitorData["inchi"], inhibitorData["description"], inhibitorData["name"]))
    mydb.commit()

    #UPDATE THE aliases_dbid TABLE
    if(inhibitorData["aliases"] != None):
        for alias in inhibitorData["aliases"]:
            databaseQuery = "SELECT drugbank_id FROM aliases_dbid WHERE alias = %s"
            cursor.execute(databaseQuery, (alias,))
            outputID = cursor.fetchone()
            if(outputID != None and len(outputID) >= 1):
                databaseQuery = "UPDATE aliases_dbid SET drugbank_id = %s WHERE alias = %s"
            else:
                databaseQuery = "INSERT INTO aliases_dbid (drugbank_id, alias) VALUES (%s, %s)"
            cursor.execute(databaseQuery, (inhibitorData["drugbankID"], alias))
            mydb.commit()


    #UPDATE THE drug_and_target table
    if(inhibitorData["targets"] != None):
        for target in inhibitorData["targets"]:
            databaseQuery = "SELECT drugbank_id FROM drug_and_target WHERE uniprot_id = %s AND drugbank_id = %s"
            cursor.execute(databaseQuery, (target, inhibitorData["drugbankID"]))
            outputID = cursor.fetchone()
            if(outputID == None or len(outputID) == 0):
                databaseQuery = "INSERT INTO drug_and_target (uniprot_id, drugbank_id) VALUES (%s, %s)"
                cursor.execute(databaseQuery, (target, inhibitorData["drugbankID"]))
                mydb.commit()
    cursor.close()

def FullUpdate():
    latestKinaseInhibitors = getKnownInhibitors()
    print("Got latest inhibitors")
    latestKinaseInhibitors = JoinDrugbankData(latestKinaseInhibitors)
    print("Got drugbank data")
    GetSpecificDrugbankData(latestKinaseInhibitors)

    print(latestKinaseInhibitors)



FullUpdate()

        