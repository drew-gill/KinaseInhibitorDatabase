#!/usr/bin/env python3
import sys
import mysql.connector
import csv
import os
import time

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="Easypassword1!",
  database="research"
)

globalStructures = None
outputDirectory = "STRUCTURAL_FILES/"
dumpSubdirectory = "DATABASE_DUMP/"
pmvPath = '"C:\Program Files (x86)\MGLTools-1.5.6\pmv.bat"'
chimeraXPath = ""
chimeraPath = ""
pymolPath = ""

#look for a drug or protein by their official name, alias, or ID. Returns the DrugBank ID (drugs) or UniProt ID (proteins)
def SearchDatabaseByName(userInput, drug_or_protein):
    mycursor = mydb.cursor()       
    if(drug_or_protein == "DRUG"):
        inputQuery = "SELECT drugbank_id FROM kinasedrugs WHERE drugbank_id = %s OR name = %s"
        mycursor.execute(inputQuery, [userInput, userInput])
    elif(drug_or_protein == "PROTEIN"):
        inputQuery = "SELECT uniprot_id FROM kinaseproteins WHERE uniprot_id = %s OR HGNC_Name = %s OR Manning_Name = %s OR Descriptive_Name = %s OR x_Name = %s"
        mycursor.execute(inputQuery, [userInput, userInput, userInput, userInput, userInput])

    outputID = mycursor.fetchone()
    mycursor.close()
    if(outputID == None or len(outputID) == 0):
        return None
    outputID = outputID[0]


    if(outputID != ""):
        return outputID
    else:
        return None

#checks if the ID (drugbank, uniprot) exists in the database 
def CheckDatabaseForID(drugbankID=None, uniprotID=None):
    mycursor = mydb.cursor()

    if(drugbankID != None):
        inputQuery = "SELECT count(*) FROM kinasedrugs WHERE drugbank_id = %s"
        mycursor.execute(inputQuery, [drugbankID])
    elif(uniprotID != None):
        inputQuery = "SELECT count(*) FROM kinaseproteins WHERE uniprot_id = %s"
        mycursor.execute(inputQuery, [uniprotID])

    count = mycursor.fetchone()
    mycursor.close()
    if(count == None or len(count) == 0):
        return None
    count = count[0]
    
    
    if(count > 0):
        return True
    else:
        return False

def GetNameFromValidID(drugbankID=None, uniprotID=None):
    stringOutput = ""
    mycursor = mydb.cursor()       
    if(drugbankID != None):
        structureQuery = "SELECT name FROM kinasedrugs WHERE drugbank_id = %s"
        mycursor.execute(structureQuery, [drugbankID])
    elif(uniprotID != None):
        structureQuery = "SELECT HGNC_Name FROM kinaseproteins WHERE uniprot_id = %s"
        mycursor.execute(structureQuery, [uniprotID])
    else:
        return stringOutput

    details = mycursor.fetchall()
    mycursor.close()
    if(details == None or len(details) == 0):
        return False
    stringOutput = details[0][0]

    return stringOutput


#returns the general information of the item in the database. Should only have protein OR drug
def GetInformationFromID(drugbankID=None, uniprotID=None):
    stringOutput = ""
    mycursor = mydb.cursor()       
    if(drugbankID != None):
        structureQuery = "SELECT name, description, chemSpider, pubchem_compound, chEMBL, INCHI_KEY, smiles, company, phase, atc FROM kinasedrugs WHERE drugbank_id = %s"
        mycursor.execute(structureQuery, [drugbankID])
    elif(uniprotID != None):
        structureQuery = "SELECT HGNC_Name, Manning_Name, descriptive_name, x_Name, bindingDBID, kinase_group, kinase_family, kinase_subfamily FROM kinaseproteins WHERE uniprot_id = %s"
        mycursor.execute(structureQuery, [uniprotID])
    else:
        return stringOutput

    details = mycursor.fetchall()
    mycursor.close()
    if(details == None or len(details) == 0):
        return False
    details = details[0]

    stringOutput = PrintInformationFromID(details, drugbankID=drugbankID, uniprotID=uniprotID)

    return stringOutput

#print the information from GetInformationFromID() according to whether it is a protein OR drug
def PrintInformationFromID(results, drugbankID=None, uniprotID=None):
    stringOutput = ""
    if(drugbankID != None):
        labels = ["Name","Description", "ChemSpider", "Pubchem Compound", "chEMBL", "INCHI", "SMILES", "Company", "Phase", "ATC Code"]
        stringOutput += ("DrugBank ID: %s\n" % drugbankID)
    elif(uniprotID != None):
        labels = ["HGNC Name", "Manning Name", "Description", "XName", "BindingDB ID", "Kinase Group", "Kinase Family", "Kinase Subfamily"]
        stringOutput += ("UniProt ID: %s\n" % uniprotID)
    else:
        stringOutput += "ID not set"

    for i, item in enumerate(results):
        if(item == None):
            item = "NULL"
        stringOutput += ("\n" + labels[i] + ": %s\n" % str(item))

    print(stringOutput)
    return stringOutput

def getAndPrintStructures(drugbankID=None, uniprotID=None, drug_or_protein=None):
    if(drug_or_protein == "BINDING" and (drugbankID == None or uniprotID == None)):
        return "To find binding structures, enter both a protein and drug identifier"
    
    structs = GetStructures(drugbankID=drugbankID, uniprotID=uniprotID, drug_or_protein=drug_or_protein)
    
    stringOutput = StructureChoice(structs, drug_or_protein)
    global globalStructures
    globalStructures = structs
    return stringOutput


#returns an array of the filename of all structures available for a drug, a protein, or a drug/protein complex
def GetStructures(drugbankID=None, uniprotID=None, drug_or_protein=None):
    mycursor = mydb.cursor()    

    if(drug_or_protein == "BINDING"):
        if(drugbankID != None and uniprotID != None):
            structureQuery = "SELECT structurefilename, drugbank_id, uniprot_id, rcsb_id FROM structuralfiles WHERE drugbank_id = %s AND uniprot_id = %s"
            mycursor.execute(structureQuery, [drugbankID, uniprotID])
        elif(drugbankID == None):
            structureQuery = "SELECT structurefilename, drugbank_id, uniprot_id, rcsb_id FROM structuralfiles WHERE drugbank_id IS NOT NULL AND uniprot_id = %s"
            mycursor.execute(structureQuery, [uniprotID])
        elif(uniprotID == None):
            structureQuery = "SELECT structurefilename, drugbank_id, uniprot_id, rcsb_id FROM structuralfiles WHERE drugbank_id = %s AND uniprot_id IS NOT NULL"
            mycursor.execute(structureQuery, [drugbankID])
    elif(drugbankID != None and drug_or_protein == "DRUG"):
        structureQuery = "SELECT structurefilename, drugbank_id, uniprot_id, rcsb_id FROM structuralfiles WHERE drugbank_id = %s AND uniprot_id IS NULL"
        mycursor.execute(structureQuery, [drugbankID])
    elif(uniprotID != None and drug_or_protein == "PROTEIN"):
        structureQuery = "SELECT structurefilename, drugbank_id, uniprot_id, rcsb_id FROM structuralfiles WHERE uniprot_id = %s AND drugbank_id IS NULL"
        mycursor.execute(structureQuery, [uniprotID])
    else:
        return None

    structs = mycursor.fetchall()
    mycursor.close()
    if(structs == None or len(structs) == 0):
        return None

    return structs

#get and print all bindings
def getAndPrintBindings(drugbankID=None, uniprotID=None):
    bindings= GetBindings(drugbankID=drugbankID, uniprotID=uniprotID)
    bindingText = PrintBindings(bindings, drugbankID=drugbankID, uniprotID=uniprotID)
    return bindingText

#returns an array of all of the bindings that a given drug/kinase has to kinases/drugs
def GetBindings(drugbankID=None, uniprotID=None):
    mycursor = mydb.cursor()    
    

    if(drugbankID != None and uniprotID != None):
        structureQuery = "SELECT uniprot_id FROM drug_and_target WHERE drugbank_id = %s AND uniprot_id = %s"
        mycursor.execute(structureQuery, [drugbankID,uniprotID])
    elif(drugbankID != None):
        structureQuery = "SELECT uniprot_id FROM drug_and_target WHERE drugbank_id = %s"
        mycursor.execute(structureQuery, [drugbankID])
    elif(uniprotID != None):
        structureQuery = "SELECT drugbank_id FROM drug_and_target WHERE uniprot_id = %s"
        mycursor.execute(structureQuery, [uniprotID])
    else:
        return None

    bindings = mycursor.fetchall()
    mycursor.close()
    if(bindings == None or len(bindings) == 0):
        return None
    for idx, binding in enumerate(bindings):
        bindings[idx] = binding[0]

    return bindings

def PrintBindings(bindings, drugbankID=None, uniprotID=None):
    stringOutput = ""
    drug_or_protein = ""

    if(drugbankID != None):
        drugName = GetNameFromValidID(drugbankID=drugbankID)
        drug_or_protein += "DRUG"
    if(uniprotID != None):
        proteinName = GetNameFromValidID(uniprotID=uniprotID)
        drug_or_protein += "PROTEIN"
    
    if(drugbankID != None and uniprotID != None):
        if(bindings != None):
            stringOutput += ("~~~ There is a noted interaction between inhibitor %s (%s) and kinase %s (%s) ~~~" %(drugbankID, drugName, uniprotID, proteinName))
        else:
            stringOutput += ("~~~ There is NO noted interaction between inhibitor %s (%s) and kinase %s (%s) ~~~" %(drugbankID, drugName, uniprotID, proteinName))
        print(stringOutput)
        return stringOutput
    elif(drugbankID != None):
        if(bindings == None):
            stringOutput += ("~~~ NO interactions available for inhibitor %s (%s) ~~~" % (drugbankID, drugName))
        else:
            stringOutput += ("~~~ Interactions with inhibitor %s (%s) ~~~" % (drugbankID, drugName))
    elif(uniprotID != None):
        if(bindings == None):
            stringOutput += ("~~~ NO interactions available for protein kinase %s (%s) ~~~" % (uniprotID, proteinName))
        else:
            stringOutput += ("~~~ Interactions with protein kinase %s (%s) ~~~" % (uniprotID, proteinName))
    else:
        stringOutput += ("No ID supplied")

    if(bindings == None or len(bindings) == 0):
        return ""
    for idx, binding in enumerate(bindings): #if the subject in question is a drug, we are printing the protein bindings, and vice versa
        if(drug_or_protein == "DRUG"):
            stringOutput += ("\n%i) %s (%s)" % (idx+1, binding, GetNameFromValidID(uniprotID=binding)))
        elif(drug_or_protein == "PROTEIN"):
            stringOutput += ("\n%i) %s (%s)" % (idx+1, binding, GetNameFromValidID(drugbankID=binding)))
        else:
            stringOutput += ("\n%i) %s (%s)" % (idx+1, binding))

    print(stringOutput)
    return stringOutput

#handles user decision based on the number of structures available
def StructureChoice(structures, drug_or_protein):
    stringOutput = ""

    if(drug_or_protein == "DRUG"):
        noStructureText = "No structures available for this inhibitor"
        oneStructureText = "One structure is available for this inhibitor. Would you like to download it?"
        manyStructureText = "There is more than one structure available for this inhibitor. Choose which one you would like to download below."
    elif(drug_or_protein == "PROTEIN"):
        noStructureText = "No structures available for this kinase protein"
        oneStructureText = "One structure is available for this kinase protein. Would you like to download it?"
        manyStructureText = "There is more than one structure available for this kinase protein. Choose which one you would like to download below."
    elif(drug_or_protein == "BINDING"):
        noStructureText = "No inhibitor/kinase complex structures available"
        oneStructureText = "One inhibitor/kinase complex structure is available. Would you like to download it?"
        manyStructureText = "There are more than one inhibitor/kinase complex structures available. Choose which one you would like to download below."


    if(structures == None or len(structures) == 0):
        stringOutput += noStructureText
    elif(len(structures) == 1 or not (isinstance(structures[0], list) or isinstance(structures[0], tuple))):
        if(isinstance(structures, list)):
            structures = structures[0]
        stringOutput += oneStructureText
        stringOutput += "\n1) "
        stringOutput += PrintDBObject(structures)
    else:
        stringOutput += manyStructureText
        for i, item in enumerate(structures):
            j = i+1
            stringOutput += ("\n%i)" % j)
            stringOutput += PrintDBObject(item)
    
    print(stringOutput)
    return stringOutput

#prints an object from the structuralfiles db
def PrintDBObject(item):
    stringOutput = ""
    stringOutput += ("\tFilename: %s" % item[0]) #filename in the DB

    if(item[1] != None):
        stringOutput += ("\n\tDrugBank ID: %s (%s)" % (item[1], GetNameFromValidID(item[1]))) #drugbank ID if available
    if(item[2] != None):
        stringOutput += ("\n\tUniProt ID: %s (%s)" % (item[2], GetNameFromValidID(item[2]))) #uniprotID if available
    if(item[3] != None):
        stringOutput += ("\n\tRCSB ID: %s" % item[3]) #RCSB ID, if available

    stringOutput += ("\n---\n")

    return stringOutput

def SaveStructureByNumber(fileNumber, openPMV):
    stringOutput = ""

    if(fileNumber > 0 and fileNumber <= len(globalStructures)):
        stringOutput += SaveStructure(globalStructures[fileNumber-1][0])
        if(openPMV == 1):
            os.system('%s %s' % (pmvPath, stringOutput))
    else:
        stringOutput += "Enter a valid file number"
    
    print(stringOutput)
    return stringOutput

#saves the given file to the output directory
def SaveStructure(fileName):
    retrieveQuery = "SELECT structure FROM structuralfiles WHERE structurefilename = %s"
    stringOutput = ""

    mycursor = mydb.cursor()       
    mycursor.execute(retrieveQuery, [fileName])
    structure = mycursor.fetchone()
    mycursor.close()
    if(structure == None or len(structure) == 0):
        return False
    structure = structure[0]

    if(structure != None):
        stringOutput += ("Saving structure file %s to %s directory" % (fileName, outputDirectory))
        fileLocation = outputDirectory + fileName
        try:
            with open(fileLocation, 'wb') as f:
                f.write(structure)
        except UnicodeDecodeError:
            structure = structure.encode()
            with open(fileLocation, 'wb') as f:
                f.write(structure)

        return fileLocation
    else:
        stringOutput += ("Error saving structure")

    return stringOutput

#gets all data stored in the database and stores it in a CSV file format
#save to OUTPUTDIR/DUMPDIR/prefix_table.csv
def DumpDataToCSV(fileName, includeStructuralFiles=False):
    tableNames = ["aliases_dbid", "drug_and_target", "kinasedrugs", "kinaseproteins"]

    if(includeStructuralFiles):
        tableNames.append("structuralfiles")

    for name in tableNames:
        query = "SELECT * FROM %s" % name

        mycursor = mydb.cursor()
        mycursor.execute(query)
        result = mycursor.fetchall()

        csvWriter = csv.writer(open(outputDirectory + dumpSubdirectory + fileName + ("_%s.csv" % name), "w", encoding="utf-8"))
        for row in result:
            csvWriter.writerow(row)


