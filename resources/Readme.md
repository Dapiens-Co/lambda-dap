## Notes

1. Proposed Datamodel - Each RuleGroup to have its rules stored in nosql table named by the RuleGroup.  


E.g  FloodCert - Table to hold records that will have all rules.
   The subrules will also be kept in the nested json object.
   Refer to the nosql_table_rules_floodcert.json
   
   
   
## Windows Mongo
Open CMD as ADMINISTRATOR

"C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" --dbpath="C:\Dev\mongodbdata\dapi1"

Open Mongo Compass and play
----------------------------
dbname : dap1
collection name: flood




