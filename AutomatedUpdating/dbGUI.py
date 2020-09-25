#!/usr/bin/python3

from tkinter import *
from tkinter import filedialog
from databaseAccessHelper import *

def helperChoice():
    proteinID = SearchDatabaseByName(proteinNameID.get(), "PROTEIN")
    drugID = SearchDatabaseByName(drugNameID.get(), "DRUG")
    newText = ""


    if(actionChoice.get() == 0):
        if(moleculeChoice.get() == "PROTEIN"):
            if(proteinID != None):
                newText = GetInformationFromID(uniprotID=proteinID)
            else:
                newText = "Enter a protein identifier OR choose a different option"
        elif(moleculeChoice.get() == "DRUG"):
            if(drugID != None):
                newText = GetInformationFromID(drugbankID=drugID)
            else:
                newText = "Enter a drug identifier OR choose a different option"
        elif(moleculeChoice.get() == "BINDING"):
            newText = getAndPrintBindings(drugbankID=drugID, uniprotID=proteinID)
    elif(actionChoice.get() == 1):
        newText = getAndPrintStructures(drugbankID=drugID, uniprotID=proteinID, drug_or_protein=moleculeChoice.get())
    
    setText(newText)

def saveHelper():
    stringOutput = ""
    try:
        num = int(fileNumber.get())
        stringOutput += SaveStructureByNumber(num, openPMV.get())
    except ValueError:
        stringOutput += "Error: make sure to input an integer"

    setText(stringOutput)

def setText(newText):
    textBox.delete(1.0, END)
    textBox.insert(END, newText)

if __name__ == '__main__':
    root = Tk()
    root.geometry("1080x720")


    actionChoice = IntVar(None, 0)
    moleculeChoice = StringVar(None, "PROTEIN")
    proteinNameID = StringVar()
    drugNameID = StringVar()
    fileNumber = StringVar()
    openPMV = IntVar()

    Label(root, text="Choose 1: ").grid(row=0, pady=10)
    Radiobutton(root, text="General Info", variable=actionChoice, value=0).grid(row=0, column=1)
    Radiobutton(root, text="Structure", variable=actionChoice, value=1).grid(row=0, column=2)
    #Radiobutton(root, text="Enter New", variable=actionChoice, value=2).grid(row=0, column=3)

    Label(root, text="Choose 1: ").grid(row=1, pady=10)
    Radiobutton(root, text="Protein", variable=moleculeChoice, value="PROTEIN").grid(row=1, column=1)
    Radiobutton(root, text="Drug", variable=moleculeChoice, value="DRUG").grid(row=1, column=2)
    Radiobutton(root, text="Binding", variable=moleculeChoice, value="BINDING").grid(row=1, column=3)

    Label(root, text="Enter ONE name/id for individual molecule info,\nBOTH for complexed molecule info: ").grid(row=2, pady=10)
    Entry(root, textvariable=proteinNameID).grid(row=2, column=1)
    Label(root, text="ID or NAME of Protein").grid(row=3, column=1)

    Entry(root, textvariable=drugNameID).grid(row=2, column=3)
    Label(root, text="ID or NAME of Drug").grid(row=3, column=3)

    Button(root, text="Submit Query", command=helperChoice).grid(row=4, column=2, pady=10)

    textBox = Text(root, height = 20, width = 100)
    textBox.grid(row=5, column=0, columnspan=4, pady=10)
    textBox.insert(END, "Submit a Query")

    Label(root, text="Download file #: ").grid(row=6, column=0, pady=10)
    Entry(root, textvariable=fileNumber).grid(row=6, column=1)
    Button(root, text="Download", command=saveHelper).grid(row=6, column=2)
    Checkbutton(root, text="Open in PMV", variable=openPMV).grid(row=6, column=3)


    root.mainloop()