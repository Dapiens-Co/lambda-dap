import copy
import json
import pymongo
import xml.etree.ElementTree as ET
from jsonpath_ng import jsonpath, parse

### ROUGH CLASS To TEST Validation Flow fetched from DB ####

## Lambda will maintain this connection over multiple calls in AWS
mgClient = pymongo.MongoClient("mongodb://localhost:27017/")

def fetchDbRules(mongoclient=mgClient,dbname='dap1',col='flood'):
    print(mongoclient.list_database_names())
    if dbname in mongoclient.list_database_names():
        print(f"Database exists : {dbname}")
    mydb = mongoclient[dbname]
    collist = mydb.list_collection_names()
    if col in collist:
        print(f"Collection exists. {col}")
    mycol = mydb[col]

    rules_cursor = mycol.find().sort("ruleId")
    ruleList = []
    for ruleRecord in rules_cursor:
        print(f" {type(ruleRecord)}  = {ruleRecord}")
        ruleList.append(ruleRecord)
    return ruleList

## ruleDict = Single Parent level rule record
## sorJsonString = JSON String not object so that JSONPath can be used
## extXmlString = XML String not object so that XPath can be used
def processRule(ruleDict ,sorJsonString , extXmlString):
    ## Isnt thread safe by the way ( But Lambda base one and one flow cud be ok )
    ruleResponse = copy.deepcopy(ruleDict)
    print(f"\n\nBEFORE PROCESSING SUBRULES : \n=============================================\n{ruleResponse}")
    #### subrules processing and updating results.
    if len(ruleDict['subRules']) > 0:
        print(f"++++ Found Subrules in RuleId : {ruleDict['ruleId']}")
        for subrule in ruleResponse['subRules']:
            subruleOutcome = processSubRule(subrule,sorJsonString , extXmlString)
            print(f"Subrule Outcome : {subruleOutcome}")
            subrule['ruleOutcomeId'] = subruleOutcome['ruleOutcomeId']
            subrule['ruleOutcomeDescription'] = subruleOutcome['ruleOutcomeDescription']
        ### End of subrule processing

    #### business rules processing - rules at parent level and no child rules.
    else:
        print(f"---- Found 0 Subrules in RuleId : {ruleDict['ruleId']}")
    print(f"AFTER PROCESSING SUBRULES : \n=============================================\n{ruleResponse}")


### return the rule with ruleoutcome block.
def processSubRule(subrule,sorJsonString , extXmlString):
    subRuleResult = copy.deepcopy(subrule)
    subRuleResult['ruleOutcomeId'] = ''
    subRuleResult['ruleOutcomeDescription'] = ''

    ### [LHS=SOR] ####### Extracting the Json data from JSONPATH in rule from SOR data  #######
    #  jsonPathAttr = '$.SystemOfRecord.CurrentSnapshot.SubjectPropertyAddress.addressLineOne'
    json_data = json.loads(sorJsonString)
    jsonPathAttr = subrule['ruleField1label']  # SystemOfRecord.CurrentSnapshot.SubjectPropertyAddress.addressLineOne
    jsonPathAttr = '$.'+jsonPathAttr
    jsonpath_expression = parse(jsonPathAttr)
    match = jsonpath_expression.find(json_data)
    print(f"type(match = {type(match)}")
    print(f" JsonPath Expression : {jsonPathAttr} \n [Find result] = {match}")
    print(f" SOR Data at JSONPATH value : ======\n {match[0].value}")
    lhsValue = match[0].value

    ### [RHS=EXT] ####### Extracting the XML data from XPATH in rule from EXT data ########
    print(f"XML StringData =\n  {extXmlString}")
    tree = ET.ElementTree(ET.fromstring(extXmlString))
    # get root element
    root = tree.getroot()
    #xmlPath = './FloodCert/SubjectPropertyAddress/addressLine1'
    xmlPath = subrule['ruleField2label']        # = External.FloodCert.SubjectPropertyAddress.addr1
    reducedXmlPath = xmlPath.split('.',1)[1]    # = FloodCert.SubjectPropertyAddress.addr1
    reducedXmlPath = './'+reducedXmlPath.replace('.','/')
    singleValueData = root.find(reducedXmlPath)
    print(f" EXT Data at Xpath : {reducedXmlPath}")
    print(f"=== value : {singleValueData.text}")
    rhsValue=singleValueData.text

    ########## Operator Based Check ##############
    ruleOperator = subrule['ruleOperator']
    ruleOutcomeId,ruleOutcomeDescription = processWithOperator(lhsValue,rhsValue,ruleOperator)
    subRuleResult['ruleOutcomeId'] =ruleOutcomeId
    subRuleResult['ruleOutcomeDescription'] =ruleOutcomeDescription
    return subRuleResult

## Issues = cannot apply for the dates..
def processWithOperator(lhsValue,rhsValue,operator):
    ruleOutcomeId,ruleOutcomeDescription='',''
    ###
    if operator=='=':
        if lhsValue==rhsValue:
            ruleOutcomeId='VAL'
            ruleOutcomeDescription='Valid'
        else:
            ruleOutcomeId = 'INV'
            ruleOutcomeDescription = 'Invalid'

    return ruleOutcomeId,ruleOutcomeDescription


## Flat file test
def fetchJsonPathValue(jsonPath):
    with open('./resources/2.1norSORinput.json') as f:
        json_data = json.load(f)
    jsonpath_expression = parse(jsonPathAttr)
    match = jsonpath_expression.find(json_data)
    print(f"JsonPath Expression Find result = {match}")
    print("Address Line1 value is", match[0].value)

## Flat file test
def parseXML(xmlfile,xpath):
    # create element tree object
    tree = ET.parse(xmlfile)
    # get root element
    root = tree.getroot()
    xmlPath = './FloodCert/SubjectPropertyAddress/addressLine1'
    singleValueData = root.find(xmlPath)
    print(f" apiCheck :   {singleValueData.text}")

if __name__ == '__main__':

    ## Hardcoded Sample - ref lambda_flood_inout.json ##
    request_body_str='''{
        "Ext": "<External><FloodCert><loanNumber>8000099876</loanNumber><NFIPInfo><communityNumber>530321</communityNumber><communityName>BURIEN, CITY OF</communityName><mapNumber>53033C0954G</mapNumber><programStatusCode>02</programStatusCode> </NFIPInfo><BasicInfo> <determinationDate>2022/10/21</determinationDate><floodZoneCode>X</floodZoneCode></BasicInfo><SubjectPropertyAddress><addressLine1>351 S 163RD ST</addressLine1><addressLine2></addressLine2><city>BURIEN</city><state>WA</state><zip>98148-5102</zip> <county>KING COUNTY</county></SubjectPropertyAddress> </FloodCert></External>",
        "SOR": {
            "SystemOfRecord": {
                "CurrentSnapshot": {
                    "loanNumber": "8000099876",
                    "SubjectPropertyAddress": {
                        "addressLineOne": "351 S 163rd St",
                        "addressLineTwo": null,
                        "city": "Burien",
                        "stateId": "WA",
                        "postalCodeId": "98148-5102",
                        "houseNumber": "351",
                        "directionPrefix": "S",
                        "streetName": "163rd",
                        "directionSuffix": null,
                        "streetSuffix": "St",
                        "apartmentUnitNumber": null,
                        "county": "KING COUNTY"
                    },
                    "SubjectPropertyFloodInfo": {
                        "floodCertificateDate": "2022-10-21",
                        "floodZoneCode": "X",
                        "nfipCommunityNumber": "530321",
                        "nfipCommunityName": "BURIEN, CITY OF",
                        "nfipMapPanelNumber": "53033C0954G",
                        "nfipCommunityStatus": "02",
                        "specialFloodHazardAreaFlag": false
                    },
                    "homeLoanKeyDates": {
                        "applicationDate": "2022-10-19"
                    }
                }
            }
        }
    }'''

    ## Proces the composite input string.. break into two slices of SOR and EXT
    composite_json_obj = json.loads(request_body_str)
    sor_obj = composite_json_obj['SOR']
    sor_json = json.dumps(sor_obj)
    print(f"SOR JSON STRING : \n=========={type(sor_json)}==============\{sor_json}")

    ext_obj = composite_json_obj['Ext']
    ext_json = json.dumps(ext_obj).strip('"')
    print(f"EXT JSON STRING : \n=========={type(ext_json)}==============\{ext_json}")

    ## Fetch db rules
    rules = fetchDbRules()  # Use defaults of params
    print(type(rules))  # String


    ####  ####
    for ruleDict in rules:
        print(f"{ruleDict.keys()}  | {ruleDict['subRules']}")
        processRule(ruleDict,sorJsonString=sor_json,extXmlString=ext_json)

    #jsonPathAttr = '$.SystemOfRecord.CurrentSnapshot.SubjectPropertyAddress.addressLineOne'
   # fetchJsonPathValue(jsonPathAttr)

   # xmlfile = "./resources/2.2norFloodCert.xml"
    #parseXML(xmlfile)
