### References

#### 1. AWS Step + Lambda + Drools Opensource
https://aws.amazon.com/blogs/compute/using-aws-step-functions-and-amazon-dynamodb-for-business-rules-orchestration/

## Notes.  
1. While comparing for = on Date natured fields.. 
  Custom implementaito needed : 
```
<determinationDate>2022/10/21</determinationDate>
"floodCertificateDate": "2022-10-21",
```

2. 2.1norSORinput.json   
  SubjectPropertyAddress.county is missing -- added manual  

3. 2.2norFloodCert.xml  
   ./FloodCert/BasicInfo/floodZoneCode element missing -- added manual  
