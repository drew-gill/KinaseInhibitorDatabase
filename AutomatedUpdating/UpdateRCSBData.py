import requests
import csv
import time
import mysql.connector
import xml.etree.ElementTree as ElementTree
import rcsbCategorizeFunctions

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="kinasedb",
  database="research"
)


def AllPotentialRCSBEntries():
    url = 'http://www.rcsb.org/pdb/rest/search'
    cursor = mydb.cursor(buffered=True)
    query = "SELECT uniprot_id FROM kinaseproteins"
    cursor.execute(query)

    kinases = cursor.fetchall()
    uniprot_rcsb = {}
    count = 0

    for id in kinases:
        count += 1
        id = id[0]
        time.sleep(0.025)

        query_text = """<?xml version="1.0" encoding="UTF-8"?>
            <orgPdbQuery>
            <queryType>org.pdb.query.simple.UpAccessionIdQuery</queryType>
            <description>Simple query for a list of Uniprot Accession IDs</description>
            <accessionIdList> %s </accessionIdList>
            </orgPdbQuery>
            """ %id

        print("Query: %s" % id)
        header = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(url, data=query_text, headers=header)

        if response.status_code == 200:
            matches = set()
            for item in response.text.split('\n'):
                item = item.split(':')
                if(item[0] != "" and item[0] != "null"):
                    matches.add(item[0])

            print("Found %d PDB entries matching query." % (len(matches)))
            if(len(matches) > 0):
                uniprot_rcsb[id] = matches
        else:
            print("Failed to retrieve results")

        print("Percent done: %.1f\n" % (100*count/len(kinases)))

    cursor.close()
    return uniprot_rcsb

def ValidLigandProteinPairs(allPotentialEntries):
    validOutput = []
    checkOutput = []

    count = 0

    cursor = mydb.cursor(buffered=True)
    for kinase in allPotentialEntries:
        count += 1
        for rcsbEntry in allPotentialEntries[kinase]:
            queryUrl = ('http://www.rcsb.org/pdb/rest/ligandInfo?structureId=%s' %rcsbEntry)
            time.sleep(0.025)
            response = requests.get(queryUrl)
            entry = ElementTree.fromstring(response.content)


            for info in entry:
                if(info.tag == 'ligandInfo'):
                    for ligand in info:
                        if(ligand.tag == 'ligand'):
                            for value in ligand:
                                if(value.tag == 'InChIKey'):
                                    #if value.text IN DB, add this structure to final list
                                    inchi_key = value.text

                                    query = ("SELECT name FROM kinasedrugs WHERE inchi_key = '%s'" %inchi_key)

                                    cursor.execute(query)
                                    # gets the number of rows affected by the command executed
                                    row_count = cursor.rowcount

                                    #make sure it has the wanted domain in the file
                                    if row_count > 0:
                                        queryURL = ('https://www.rcsb.org/pdb/rest/describePDB?structureId=%s' %rcsbEntry) #querying for the title of the entry.
                                        #Here, we are looking for "KINASE DOMAIN" being present somewhere in title in some form
                                        time.sleep(0.025)
                                        descriptionResponse = requests.get(queryURL)
                                        entry = ElementTree.fromstring(descriptionResponse.content)

                                        for info in entry:
                                            description = info.get('title')
                                                
                                            if(description is None):
                                                continue
                                            else:
                                                #print(description)
                                                description = description.lower()

                                                shouldInclude = rcsbCategorizeFunctions.narrowToKinase(description)


                                                if(shouldInclude is True):
                                                    print ("Uniprot: %s, RCSB: %s, InChI: %s" %(kinase, rcsbEntry, inchi_key))
                                                    validOutput.append([kinase, rcsbEntry, inchi_key])
                                                elif(shouldInclude == "CHECK"):
                                                    print ("Uniprot: %s, RCSB: %s, InChI: %s ~~CHECK~~" %(kinase, rcsbEntry, inchi_key))
                                                    checkOutput.append([kinase, rcsbEntry, inchi_key])
        print("Percent done: %.1f\n" % (100*count/len(allPotentialEntries)))

    return [validOutput, checkOutput]

ValidLigandProteinPairs(AllPotentialRCSBEntries())

