#!/usr/bin/env python3
import re
import os
import sys
from os import listdir
from os.path import isfile, join
from argparse import ArgumentParser
from subprocess import call

folder = ""
filecount = 999
recordcount = 99999999

def extractLine(line):
    recordLastUpdated = ""
    recordReplaced = ""
    abnStatus = ""
    abnStatusDate = ""
    abnNumber = ""
    entityTypeIND = ""
    entityTypeText = ""
    nameType = ""
    nameText = ""
    state = ""
    postcode = ""
    asicType = ""
    asicNumber = ""
    gstStatus = ""
    gstStatusDate = ""
    dgrStatusDate = ""
    dgrNameType = ""
    dgrNameText = ""
    oeEntry = ""

    p = re.compile('<ABR recordLastUpdatedDate="(\d{8})" replaced="(\w)">')
    m = p.search(line)
    if (m == None): return
    recordLastUpdated = m.groups()[0]
    recordReplaced = m.groups()[1]

    p = re.compile('<ABN status="(\w{3})" ABNStatusFromDate="(\d{8})">(\d{0,20})')
    m = p.search(line)
    abnStatus = m.groups()[0]
    abnStatusDate = m.groups()[1]
    abnNumber = m.groups()[2]

    p = re.compile('<EntityTypeInd>(\w{0,4})')
    m = p.search(line)
    entityTypeIND = m.groups()[0]

    p = re.compile('<EntityTypeText>((\w|\s){0,100})')
    m = p.search(line)
    entityTypeText = m.groups()[0]

    p = re.compile('<MainEntity>(.*?)</MainEntity>')
    m = p.search(line)
    if (m != None):
        mainEntity = m.groups()[0]
        entity = mainEntity
        p = re.compile('<NonIndividualName type="(\w{0,3})')
        m = p.search(mainEntity)
        nameType = m.groups()[0]
        p = re.compile('<NonIndividualNameText>(.{0,})</NonIndividualNameText>')
        m = p.search(mainEntity)
        nameText = m.groups()[0]
    else:
        p = re.compile('<LegalEntity>(.*?)</LegalEntity>')
        m = p.search(line)
        legalEntity = m.groups()[0]
        entity = legalEntity
        p = re.compile('<IndividualName type="(\w{0,99})')
        m = p.search(legalEntity)
        nameType = m.groups()[0]
        p = re.compile('<NameTitle>([\w|\s]{0,50})')
        m = p.search(legalEntity)
        nameTitle = ""
        if (m != None): nameTitle = m.groups()[0]
        p = re.compile('<GivenName>([\w|\s]{0,100})')
        m = p.search(legalEntity)
        givenNames = ""
        if (m != None): givenNames = " ".join(m.groups())
        p = re.compile('<FamilyName>([\w|\s]{0,50})')
        m = p.search(legalEntity)
        familyNames = ""
        if (m != None): familyNames = " ".join(m.groups())
        nameText = ""
        if (nameTitle): nameText = nameText + nameTitle
        if (givenNames): nameText = nameText + " " + givenNames
        if (familyNames): nameText = nameText + " " + familyNames

    p = re.compile('<State>(\w{0,3})')
    m = p.search(entity)
    state = m.groups()[0]
    p = re.compile('<Postcode>(\d{0,50})')
    m = p.search(entity)
    postcode = m.groups()[0]

    p = re.compile('<ASICNumber ASICNumberType="(\w{0,99})">(\d{9})')
    m = p.search(line)
    if (m != None):
        asicType = m.groups()[0]
        asicNumber = m.groups()[1]

    p = re.compile('<GST status="(\w{0,99})" GSTStatusFromDate="(\d{8})"')
    m = p.search(line)
    gstStatus = m.groups()[0]
    gstStatusDate = m.groups()[1]

    p = re.compile('<DGR DGRStatusFromDate="(\d{8})?">(.*?)</DGR>')
    m = p.search(line)
    if (m != None):
        dgrStatusDate = m.groups()[0]
        dgr = m.groups()[1]
        if (dgr != None):
            p = re.compile('<NonIndividualName type="(\w{0,3})')
            m = p.search(dgr)
            dgrNameType = m.groups()[0]

            p = re.compile('<NonIndividualNameText>(.{0,})</NonIndividualNameText>')
            m = p.search(dgr)
            dgrNameText = m.groups()[0]

    p = re.compile('<OtherEntity>.*?</OtherEntity>')
    m = p.findall(line)
    oeEntry = ""
    if m:
        otherEntities = m
        for oEntity in otherEntities:
            p = re.compile('<NonIndividualName type="(\w{0,3})')
            m = p.search(oEntity)
            oeNameType = m.groups()[0]
            p = re.compile('<NonIndividualNameText>(.{0,})</NonIndividualNameText>')
            m = p.search(oEntity)
            oeNameText = m.groups()[0]
            oeEntry = oeEntry + str(otherEntities.index(oEntity)+1) + ". " + oeNameType + "-" + oeNameText + " "
    
    nameText = '"' + nameText.replace('"','""').strip() + '"'
    entityTypeText = '"' + entityTypeText.replace('"','""').strip() + '"'
    dgrNameText = '"' + dgrNameText.replace('"','""').strip() + '"'
    oeEntry = '"' + oeEntry.replace('"','""').strip() + '"'
    fields = [recordLastUpdated, recordReplaced,
                    abnStatus, abnStatusDate, abnNumber,
                    entityTypeIND, entityTypeText,
                    nameType, nameText, state, postcode,
                    asicType, asicNumber,
                    gstStatus, gstStatusDate,
                    dgrNameType, dgrNameText, dgrStatusDate,
                    oeEntry]
    csvLine = ','.join(fields)
    return csvLine

def readData():
    dataFiles = sorted([f for f in listdir(folder) if isfile(join(folder, f))])
    fcount = 0
    print('\nProcessing files in folder "' + folder + '"\n')
    for dataFile in dataFiles:
        if (fcount == filecount): break
        outFile = open(dataFile + '-output.csv', 'w')
        outFile.write('recordLastUpdated,recordReplaced,abnStatus,abnStatusDate,abnNumber,entityTypeIND,entityTypeText,nameType,nameText,state,postcode,asicType,asicNumber,gstStatus,gstStatusDate,dgrNameType,dgrNameText,dgrStatusDate,otherEntities\n')

        lcount = 0
        rcount = 0
        with open(join(folder, dataFile)) as fileobject:
            print("File " + str(fcount+1) + ". " + dataFile + '')
            totalRecords = ""
            for line in fileobject:
                if (rcount == recordcount): break
                if (lcount == 0):
                    p = re.compile('<RecordCount>(.*?)</RecordCount>')
                    m = p.search(line)
                    totalRecords = m.groups()[0]
                if (recordcount == 99999999 or recordCount >= totalRecords):
                    targetRecords = totalRecords
                else: targetRecords = str(recordcount)

                csvLine = extractLine(line)
                if (csvLine):
                    msg = " Entry  " + str(rcount+1) + " of " + targetRecords
                    sys.stdout.write(('\b' * len(msg)) + msg)
                    outFile.write(csvLine + '\n')
                    rcount = rcount + 1
                lcount = lcount + 1
                print('   --> ' + dataFile + '-output.csv')
                sys.stdout.write("\033[F")
            print("\r\n")
        fcount = fcount + 1
        outFile.close()

if __name__ == '__main__':
    argparser = ArgumentParser(description='Process bulk XML data.')
    argparser.add_argument('--folder', default=folder, type=str, required=True, help='The folder with the XML data files.')
    argparser.add_argument('--filecount', default=filecount, type=int, required=False, help='How many of the files to process starting from the first found.')
    argparser.add_argument('--recordcount', default=recordcount, type=int, required=False, help='How many records to extract starting from the first found.')
    cmd = vars(argparser.parse_args())
    folder=cmd['folder']
    filecount=cmd['filecount']
    recordcount=cmd['recordcount']
    readData()
