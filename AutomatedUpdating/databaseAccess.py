#!/usr/bin/env python3
import sys
import mysql.connector
import csv
from databaseAccessHelper import *

loggingIn = True
while(loggingIn):
    rootPwd = input("Input the root password for the database\n Your input: ")

    try:
        mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd= rootPwd,
        database="research"
        )

        loggingIn = False
    except:
        print("Password not accepted! Please try again\n")


while(True):
    userIn1 = input("""\nWhat would you like to do?\n
    1) View GENERAL information about an protein kinase or inhibitor by its name or ID\n
    2) View STRUCTURAL information about an inhibitor, a kinase, or their binding\n
    3) Add new data to the database about an inhibitor, a kinase, or their binding\n
    4) Exit\n
 Your input: """)

#General information
    if(userIn1 == "1"):
        while(True):
            userIn2 = input("""\nWhich type of entry would you like to get general info about?\n
                1) Protein Kinase\n
                2) Small-Molecule Inhibitor\n
                3) Exit\n
                 Your input: """)

            if(userIn2 == "1"):
                userIn3 = input("Enter the protein kinase (name or ID) you would like to search for\n Your input: ")
                id = SearchDatabaseByName(userIn3, "PROTEIN")
                if(id is not None):
                    print("Found! Information will be printed below.\n")
                    GetInformationFromID(uniprotID=id)
                elif(CheckDatabaseForID(uniprotID=userIn3)):
                    print("Found! Information will be printed below.\n")
                    GetInformationFromID(uniprotID=userIn3)
                else:
                    print("Protein Kinase not found in the database. Try checking the spelling or look up UniProt ID")

                input("\n--Press enter to continue--\n")
            elif(userIn2 == "2"):
                userIn3 = input("Enter the inhibitor (name or ID) you would like to search for\n Your input: ")
                id = SearchDatabaseByName(userIn3, "DRUG")
                if(id is not None):
                    print("Found! Information will be printed below.\n")
                    GetInformationFromID(drugbankID=id)
                elif(CheckDatabaseForID(drugbankID=userIn3)):
                    print("Found! Information will be printed below.\n")
                    GetInformationFromID(drugbankID=userIn3)
                else:
                    print("Inhibitor not found in the database. Try checking the spelling or look up DrugBank ID")

                input("\n--Press enter to continue--\n")
            elif(userIn2 == "3"):
                break
            else:
                print("Invalid input! Please enter one of the menu options")
                input("\n--Press enter to continue--\n")

#Structural information
    elif(userIn1 == "2"):
        while(True):
            userIn2 = input("""\nWhat would you like to do?\n
    1) Get structure of UNBOUND inhibitor\n
    2) Get structure of UNBOUND kinase\n
    3) Get structure of BOUND inhibitor with kinase\n
    4) Get all interactions available for an inhibitor\n
    5) Get all interactions available for kinase\n
    6) Exit this menu\n
 Your input: """)

            if(userIn2 == "1"):
                userIn3 = input("Enter the DrugBank ID of the inhibitor you want the UNBOUND structure of\n Your input: ")
                if(CheckDatabaseForID(drugbankID=userIn3)):
                    allStructures = GetStructures(drugbankID=userIn3)
                    StructureChoice(allStructures, "DRUG")
                else:
                    print("Inhibitor not found!")
                input("\n--Press enter to continue--\n")
            elif(userIn2 == "2"):
                userIn3 = input("Enter the UniProt ID of the protein kinase you want the UNBOUND structure of\n Your input: ")
                if(CheckDatabaseForID(uniprotID=userIn3)):
                    allStructures = GetStructures(uniprotID=userIn3)
                    StructureChoice(allStructures, "PROTEIN")
                else:
                    print("Kinase not found!")
                input("\n--Press enter to continue--\n")
            elif(userIn2 == "3"):
                while(True):
                    userIn3 = input("""\nWhat would you like to do?\n
                        1) Search for all available bindings for an INHIBITOR\n
                        2) Search for all available bindings for a PROTEIN KINASE\n
                        3) Search for a specific drug/kinase binding\n
                        4) Exit this menu\n
                    Your input: """)


                    if(userIn3 == "1"):
                        userIn4 = input("Enter the DrugBank ID of the inhibitor you want to the all available bound structures for\n Your input: ")
                        if(CheckDatabaseForID(drugbankID=userIn4)):
                            allStructures = GetStructures(drugbankID=userIn4, uniprotID="SEARCH")
                            StructureChoice(allStructures, "BOTH")
                        else:
                            print("Inhibitor not found!")

                        input("\n--Press enter to continue--\n")
                    elif(userIn3 == "2"):
                        userIn4 = input("Enter the UniProt ID of the protein kinase you want to the see all available bound structures for\n Your input: ")
                        if(CheckDatabaseForID(uniprotID=userIn4)):
                            allStructures = GetStructures(drugbankID="SEARCH", uniprotID=userIn4)
                            StructureChoice(allStructures, "BOTH")
                        else:
                            print("Kinase not found!")

                        input("\n--Press enter to continue--\n")
                    elif(userIn3 == "3"):
                        userIn4 = input("Enter the DrugBank ID of the inhibitor you want to the see all available bound structures for\n Your input: ")
                        if(CheckDatabaseForID(drugbankID=userIn4)):
                            userIn5 = input("Enter the UniProt ID of the protein kinase you want to see all available bound structures for\n Your input: ")
                            if(CheckDatabaseForID(uniprotID=userIn5)):
                                allStructures = GetStructures(drugbankID=userIn4, uniprotID=userIn5)
                                StructureChoice(allStructures, "BOTH")
                            else:
                                print("Kinase not found!")
                        else:
                            print("Inhibitor not found!")
                        
                        input("\n--Press enter to continue--\n")
                    elif(userIn3 == "4"):
                        break
                    else:
                        print("Please enter a valid entry number!\n")
                        input("\n--Press enter to continue--\n")
            
            elif(userIn2 == "4"):
                userIn3 = input("Enter the DrugBank ID of the inhibitor you want to the see all available kinase interactions for\n Your input: ")
                if(CheckDatabaseForID(drugbankID=userIn3)):
                    allBindings = GetBindings(drugbankID=userIn3)
                    PrintBindings(allBindings, drugbank_id=userIn3)
                else:
                    print("Inhibitor not found!")
                
                input("\n--Press enter to continue--\n")
                
            elif(userIn2 == "5"):
                userIn3 = input("Enter the UniProt ID of the protein kinase you want to the see all available inhibitor interactions for\n Your input: ")
                if(CheckDatabaseForID(uniprotID=userIn3)):
                    allBindings = GetBindings(uniprotID=userIn3)
                    PrintBindings(allBindings, uniprot_id=userIn3)
                else:
                    print("Kinase not found!")

                input("\n--Press enter to continue--\n")

            elif(userIn2 == "6"):
                break
            else:
                print("Please enter a valid entry number!\n")
                input("\n--Press enter to continue--\n")

    elif(userIn1 == "3"):
        while(True):
            userIn2 = input("""What type of data would you like to insert into the database?\n
                1) General information on a protein kinase or an inhibitor\n
                2) Binding data between protein kinases and inhibitors\n
                3) Structural files for a noncomplexed protein kinase, a noncomplexed inhbitor, or a complexed kinase/inhibitor pair.\n
                4) Exit\n
            Your input: """)

            if(userIn2 == "1"):
                InsertGeneralData()
            elif(userIn2 == "2"):
                InsertBindingData()
            elif(userIn3 == "3"):
                InsertStructuralFile()
            elif(userIn4 == "4"):
                break
            else:
                print("Please enter a valid entry number!\n")
                input("\n--Press enter to continue--\n")

    elif(userIn1 == "4"):
        print("\nExiting...\n")
        break
    else:
        print("Invalid input! Please enter one of the menu options")
        input("\n--Press enter to continue--\n")