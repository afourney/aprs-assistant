import sqlite3  
import zipfile
import io
import sys
  
# Define the database filename and data files  
db_filename = 'fcc_uls.db'  
amat_filename = "l_amat.zip"
gmrs_filename = "l_gmrs.zip"
en_data_filename = 'EN.dat'  
am_data_filename = 'AM.dat'  
  
# SQL query to create the "EN" table  
create_en_table_query = """  
CREATE TABLE IF NOT EXISTS EN (  
    Service VARCHAR(5),
    Unique_System_Identifier VARCHAR(9),  
    ULS_File_Number VARCHAR(14),  
    EBF_Number VARCHAR(30),  
    Call_Sign VARCHAR(10),  
    Entity_Type VARCHAR(2),  
    Licensee_ID VARCHAR(9),  
    Entity_Name VARCHAR(200),  
    First_Name VARCHAR(20),  
    MI VARCHAR(1),  
    Last_Name VARCHAR(20),  
    Suffix VARCHAR(3),  
    Phone VARCHAR(10),  
    Fax VARCHAR(10),  
    Email VARCHAR(50),  
    Street_Address VARCHAR(60),  
    City VARCHAR(20),  
    State VARCHAR(2),  
    Zip_Code VARCHAR(9),  
    PO_Box VARCHAR(20),  
    Attention_Line VARCHAR(35),  
    SGIN VARCHAR(3),  
    FCC_Registration_Number VARCHAR(10),  
    Applicant_Type_Code VARCHAR(1),  
    Applicant_Type_Code_Other VARCHAR(40),  
    Status_Code VARCHAR(1),  
    Status_Date VARCHAR(10), -- Assuming ISO 8601 format 'YYYY-MM-DD'  
    GHz_License_Type_3_7 VARCHAR(1),  
    Linked_Unique_System_Identifier VARCHAR(9),  
    Linked_Call_Sign VARCHAR(10)  
);  
"""

create_am_table_query = """  
CREATE TABLE IF NOT EXISTS AM (
    Unique_System_Identifier VARCHAR(9),
    ULS_File_Number VARCHAR(14),
    EBF_Number VARCHAR(30),
    Call_Sign VARCHAR(10),
    Operator_Class VARCHAR(1),
    Group_Code VARCHAR(1),
    Region_Code VARCHAR(1),
    Trustee_Call_Sign VARCHAR(10),
    Trustee_Indicator VARCHAR(1),
    Physician_Certification VARCHAR(1),
    VE_Signature VARCHAR(1),
    Systematic_Call_Sign_Change VARCHAR(1),
    Vanity_Call_Sign_Change VARCHAR(1),
    Vanity_Relationship VARCHAR(12),
    Previous_Call_Sign VARCHAR(10),
    Previous_Operator_Class VARCHAR(1),
    Trustee_Name VARCHAR(50)
);
"""  

create_view = """
CREATE VIEW IF NOT EXISTS CallSignView AS
SELECT
    EN.Unique_System_Identifier,
    EN.ULS_File_Number,
    EN.Call_Sign,
    EN.Entity_Type,
    EN.Entity_Name,
    EN.First_Name,
    EN.MI AS Middle_Initial,
    EN.Last_Name,
    EN.Street_Address,
    EN.City,
    EN.State,
    EN.Zip_Code,
    EN.Status_Code,
    EN.Status_Date,
    EN.Linked_Call_Sign,
    AM.Operator_Class,
    AM.Group_Code,
    AM.Region_Code
FROM EN
    LEFT OUTER JOIN AM ON EN.Unique_System_Identifier = AM.Unique_System_Identifier;
"""

  
# Connect to the SQLite database  
conn = sqlite3.connect(db_filename)  
cursor = conn.cursor()  
  
# Create the "EN" table  
cursor.execute(create_en_table_query)  
cursor.execute(create_am_table_query)  
cursor.execute(create_view)  
  
# Function to insert records into the "EN" table  
def insert_en_record(record):  
    insert_query = """  
    INSERT INTO EN (  
        Service,
        Unique_System_Identifier,
        ULS_File_Number,
        EBF_Number,
        Call_Sign,
        Entity_Type,  
        Licensee_ID,
        Entity_Name,
        First_Name,
        MI,
        Last_Name,
        Suffix,
        Phone,
        Fax,
        Email,
        Street_Address,  
        City,
        State,
        Zip_Code,
        PO_Box,
        Attention_Line,
        SGIN,
        FCC_Registration_Number,
        Applicant_Type_Code,
        Applicant_Type_Code_Other,
        Status_Code,
        Status_Date,
        GHz_License_Type_3_7,
        Linked_Unique_System_Identifier,  
        Linked_Call_Sign  
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);  
    """  
    cursor.execute(insert_query, record)  

# Function to insert records into the "AM" table  
def insert_am_record(record):  
    insert_query = """  
    INSERT INTO AM (  
        Unique_System_Identifier,
        ULS_File_Number,
        EBF_Number,
        Call_Sign,
        Operator_Class,  
        Group_Code,
        Region_Code,
        Trustee_Call_Sign,
        Trustee_Indicator,
        Physician_Certification,
        VE_Signature,  
        Systematic_Call_Sign_Change,
        Vanity_Call_Sign_Change,
        Vanity_Relationship,
        Previous_Call_Sign,  
        Previous_Operator_Class,
        Trustee_Name  
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);  
    """  
    cursor.execute(insert_query, record) 

# Read the files add the rows
with zipfile.ZipFile(amat_filename, 'r') as zh:
    with zh.open(en_data_filename) as file:
        for line in io.TextIOWrapper(file, encoding='utf-8'):
            record = line.strip().split('|')[1:]  
            if len(record) != 29:
                sys.stderr.write("Warning. Wrong number of EN columns: " + line)
                continue
            insert_en_record(["AMAT"] + record)  

with zipfile.ZipFile(gmrs_filename, 'r') as zh:
    with zh.open(en_data_filename) as file:
        for line in io.TextIOWrapper(file, encoding='utf-8'):
            record = line.strip().split('|')[1:]  
            if len(record) != 29:
                sys.stderr.write("Warning. Wrong number of EN columns: " + line)
                continue
            insert_en_record(["GMRS"] + record)  

with zipfile.ZipFile(amat_filename, 'r') as zh:
    with zh.open(am_data_filename) as file:
        for line in io.TextIOWrapper(file, encoding='utf-8'):
            record = line.strip().split('|')[1:]  
            if len(record) != 17:
                sys.stderr.write("Warning. Wrong number of AM columns: " + line)
                continue
            insert_am_record(record)  
  
# Commit the transaction and close the connection  
conn.commit()  
conn.close()
