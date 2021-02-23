import requests
import csv
import time
import xml.etree.ElementTree as ElementTree
import mysql.connector
import os
import re
import rcsbCategorizeFunctions

###I've been experimenting with different ways of narrowing my search down to specifically the kinase 
# domains of all of the protein structures I'm compiling. Unfortunately, RCSB and the like don't seem 
# to offer any straightforward way of doing this since their narrowest classification is "transferase" 
# and sometimes "phosphotransferase", but these aren't quite specific enough for kinases. However, I've 
# noticed that in many cases, the title of the article or protein entry describes the domain of the 
# structure (and if it doesn't, it often is the full protein structure). Using this knowledge, 
# I parsed RCSB for all of the domains present in these entries and compiled them in this list.
exclude = ["ph", "dh ph", "terminal", "membrane", "tm", "fibronectin", "c2", "sh3", "frb", 
                "binding", "sensor", "tm", "extracellular", "transmembrane", "sh2",
                "sam", "bar", "homology", "et", "ig", "trkaig2", "repeat", "autoinhibitory", "pb1",
                "fn3", "card", "ferm", "box", "sarah", "pb3", "cct1", "immunoglobulin", "kringle",
                "ig58", "ig57", "ig59", "discoidin", "executioner", "death", "bromo", "fatc", "hr1b",
                "motif", "juxtamembrane", "ubiquitin", "wd40", "2", "psi", "start", "coil", "dcx",
                "d2", "targeting", "luminal", "a168", "a169", "a170", "sh2 sh3", "sh3 sh2", "auto regulatory",
                "ubiquitin associated", "beta tm", "pas", "amyloid", "igcam3", "card", "bmp", "sh3 sh2 linker regulatory",
                "ptb", "i1", "pdz", "guanine exchange factor", "tm jm", "fat", "focal adhesion targeting",
                "tetratricopeptide repeat", "a band", "ig tandem", "itk sh3", "m1", "i27", "m5", "a3",
                "a71", "i9 i11 tandem", "i9", "i11", "ecto", "i set", "c", "rapamycin binding"]
notable = ["kinase", "catalytic", "putative"]
domainSynonyms = ["domain", "domains", "segment", "region", "subunit", "module", "motif", "filament"]

def containsDomainWord(input):
    return (input in domainSynonyms or "domain" in input)

def printDomainType(title):
    if("domain" in title):
        if(title[title.index("domain") - 1] == "like"):
            print(title[title.index("domain") - 2] + "-like")
        else:
            print(title[title.index("domain") - 1])

#determine if the item in the sentence is followed by "like" or "domain"
#returns TRUE if you want to EXCLUDE this, FALSE if it should be kept
def excludeDomainsHelper(title, exclusion):
    splitEx = re.split(r'[;,()/\-\s]\s*', exclusion) # split with delimiters comma, semicolon, parenthesis, space 
    exclusionLength = len(splitEx)


    if(splitEx[0] in title): #check if the title contains the first word of the exclusion
        firstIndex = title.index(splitEx[0]) #index of the first word of the exclusion in the title

        if(len(splitEx) > 1): #make sure the whole exclusion is contained
            for idx, word in enumerate(splitEx):
                if(splitEx[idx] in title):
                    if(not title.index(splitEx[idx]) == firstIndex + idx):
                        return False
                else:
                    return False
        lastIndex = firstIndex + (exclusionLength - 1)
    
    else: #do not exclude if the exclusion or the exclusion-domain cannot be found 
        exclusion = exclusion + "domain"
        if(exclusion not in title):
            return False
        else:
            return True


    if(lastIndex == len(title)-1): #last word in the list
        return "CHECK"
        
    if(title[lastIndex+1] == "like" and containsDomainWord(title[lastIndex+2])):
        return True
    if(containsDomainWord(title[lastIndex+1]) or containsDomainWord(title[firstIndex-1])): #covers "domain", "domains", etc. Directly before or after the exclusion
        return True
    else:
        return "CHECK" #doesn't directly say domain or the like before or after, but still contains an exclusion. check later.

def excludeDomains(title):
    #printDomainType(title)

    for exclusion in exclude:
        result = excludeDomainsHelper(title, exclusion)
        if(result is True):
            return False
        elif(result == "CHECK"):
            return result
    else:
        return True

def checkNotableDomains(title):
    for domain in notable:
        if(domain in title):
            return True
    return False


def narrowToKinase(title):
    if("kinase domain" in title):
        return True
    else:
        title = re.split(r'[;,()/\-\s]\s*', title) # split with delimiters comma, semicolon, parenthesis, space 
        # followed by any amount of extra whitespace.

        noExclusions = rcsbCategorizeFunctions.excludeDomains(title) #determine whether the entry is allowed, disallowed, or needs further review
        possibleNotableDomains = rcsbCategorizeFunctions.checkNotableDomains(title) #determine whether the description has "catatlytic", "kinase", etc

        if(noExclusions is True):
            return True
        elif(noExclusions == "CHECK" or possibleNotableDomains):
            return "CHECK"
        else:
            return False
        