import glob, os, time
import io
import unicodedata
import re
import rake
import MySQLdb
import smtplib

from cStringIO import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

#set Google API key and Custom Search Engine ID
my_api_key = "your API key"
my_cse_id = "your CSE ID"

#initialize the stopwords list
stoppath = "SmartStoplist.txt"

#set directory for the files
my_directory = sys.argv[1]
os.chdir(my_directory)

#module to convert pdf to text
def convert(fname):
    codec = 'utf-8'
    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, codec=codec, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)
    count = 0
    infile = file(fname, 'rb')
    for page in PDFPage.get_pages(infile):
        interpreter.process_page(page)
        count = count + 1
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close
    return text, count

#module to implement rake
def rake_call(final_string, page_no):
    min_chars = 5
    max_words = 5
    if page_no <= 10:
        min_freq = 2
    elif page_no <= 30:
        min_freq = 3
    elif page_no <= 100:
        min_freq = 4
    else:
        min_freq = 8
    
    rake_object = rake.Rake(stoppath, min_chars, max_words, min_freq)
#   print "Rake call: (stoppath, %s, %s, %s )" % (min_chars, max_words, min_freq) 
    keywords = rake_object.run(final_string)
    return post_process(keywords)

#module to remove unicode characters if any
def post_process(keywords):
    keywords1 = []
    keywords2 = []
    for j in range(0, len(keywords)):
        if re.search(r' \\x.. ', repr(keywords[j][0])) is not None:
            kstart = re.search(r' \\x.. ', repr(keywords[j][0])).start()
            kend =re.search(r' \\x.. ', repr(keywords[j][0])).end()
            start_phrase = repr(keywords[j][0])[1:kstart]
            end_phrase = repr(keywords[j][0])[kend:-1]
            keywords2.append(start_phrase)
            keywords2.append(end_phrase)
        else:
            keywords1.append(keywords[j][0])

    keywords = keywords1 + keywords2
    keyword_limit = min(len(keywords), 15)
    keyword_string = ""
    for i in range(0, keyword_limit):
        keywords[i] = re.sub(r'\\x..', "", repr(keywords[i]))
        keyword_string = keyword_string + keywords[i] + " "
    keyword_string = keyword_string.replace("'", '"')
    return keyword_string
    
#module to process unicode text to string text
def preprocess(infile):
    pdf_string, page_no = convert(infile)
    decoded_string = pdf_string.decode('utf-8', 'ignore')
    normalized_string = unicodedata.normalize("NFKD", decoded_string)
    final_string = normalized_string.encode('ascii', 'replace')
    return rake_call(final_string, page_no)

#module to perform google search
def google_search(search_term, api_key, cse_id):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id).execute()
    total_results = int(res['searchInformation']['totalResults'])
    if total_results == 0:
        return ""
    else:
        return res['items']

#module to send email when no document is found on the Internet
def send_email_not_found():
    fromaddr = "from email address"
    toaddr = [ "to email address"]
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddr)
    msg['Subject'] = "Document Search - No Documents Found"
    body = "We searched the Internet and did not find any documents today."
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "password for from-email address")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

#module to send email when no document is found on the Internet
def send_email_found(body_text):
    fromaddr = "from email address"
    toaddr = [ "to email address"]
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddr)
    msg['Subject'] = "Document Search - Documents Found on Google"
    body = "We searched the Internet and found some results matching your document.\n\n"
    body += "Click on the below link to see the results:- \n"
    body += "http://localhost/ \n\n"
    #body += body_text
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "password for from-email address")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

#module to get last modified date for a file from database
def execute_select_file(filename):
    sql = "SELECT * FROM FILES \
       WHERE filename = '%s'" % (infile)
    try:
       # Execute the SQL command
       cursor.execute(sql)
       if not cursor.rowcount:
           print "No results found"
           return "", ""
       else:
           for row in cursor:
               print row[1], row[2]
               last_mod_time = row[1]
               keywords = row[2]
               return last_mod_time, keywords
    except:
        print "Error: unable to fetch data"

#module to insert file details in Files table
def execute_insert_file(infile, file_mod_time, keyword_string, current_timestamp):
    print "insert files mysql"
    sql = "INSERT INTO Files(filename, \
       last_modified, keywords, run_date) \
       VALUES ('%s', '%s', '%s', '%s' )" % \
       (infile, file_mod_time, keyword_string, current_timestamp )
    try:
       # Execute the SQL command
       cursor.execute(sql)
       # Commit your changes in the database
       db.commit()
    except:
       # Rollback in case there is any error
       db.rollback()

#module to insert file details in Files table
def execute_update_file(infile, file_mod_time, keyword_string, current_timestamp):
    print "update files mysql"
    sql = "UPDATE Files SET last_modified = '%s', \
            keywords = '%s', run_date = '%s' WHERE filename = '%s'" % \
            (file_mod_time, keyword_string, current_timestamp, infile)
    try:
       # Execute the SQL command
       cursor.execute(sql)
       # Commit your changes in the database
       db.commit()
    except:
       # Rollback in case there is any error
       db.rollback()

#module to get last modified date for a file from database
def execute_select_filesearch(filename, result_link):
    sql = "SELECT search_status FROM FileSearch \
       WHERE filename = '%s' and search_result = '%s'" % (filename, result_link)
    try:
       # Execute the SQL command
       cursor.execute(sql)
       if not cursor.rowcount:
           print "No results found"
           return ""
       else:
           for row in cursor:
               print row[0]
               search_status = row[0]
               return search_status
    except:
        print "Error: unable to fetch data"

#module to insert search details in FileSearch table
def execute_insert_filesearch(infile, result, current_timestamp, status):
    print "insert filesearch mysql"
    sql = "INSERT INTO FileSearch(filename, \
       search_result, search_status, search_date) \
       VALUES ('%s', '%s', '%s', '%s' )" % \
       (infile, result, status, current_timestamp )
    try:
       # Execute the SQL command
       cursor.execute(sql)
       # Commit your changes in the database
       db.commit()
    except:
       # Rollback in case there is any error
       db.rollback()

    
# Open database connection
db = MySQLdb.connect("localhost","mysql username","mysql password","TESTDB" )

# prepare a cursor object using cursor() method
cursor = db.cursor()

body_text = ""
for infile in glob.glob("*.pdf"):
    print "Filename: ", infile
    db_last_mod_time, keyword_string = execute_select_file(infile)
    print "DB time: %s" % db_last_mod_time
    file_mod_time = datetime.fromtimestamp(os.stat(infile).st_mtime)
    file_mod_time = file_mod_time.replace(microsecond=0)
    print "Last modified: %s" % file_mod_time
    current_timestamp = datetime.now()
    current_timestamp = current_timestamp.replace(microsecond=0)
    if db_last_mod_time == "":
        keyword_string = preprocess(infile)
        print "Keywords: ", keyword_string
        execute_insert_file(infile, file_mod_time, keyword_string, current_timestamp)
    else:
        if file_mod_time > db_last_mod_time:
            keyword_string = preprocess(infile)
            print "Keywords: ", keyword_string
            execute_update_file(infile, file_mod_time, keyword_string, current_timestamp)
        
    results = google_search(keyword_string, my_api_key, my_cse_id)
    if results != "":
        for result in results:
            db_search_status = execute_select_filesearch(infile, result['link'])
            if db_search_status == "ignore":
                execute_insert_filesearch(infile, result['link'], current_timestamp, 'ignore')
            else:
                execute_insert_filesearch(infile, result['link'], current_timestamp, 'wait')
                body_text += "Document Name: %s\nSearch result: %s\n" %(infile,result['link'])
    print "-------------------------------------------------------------"

# disconnect from server
db.close()

# send email if any document is found on google search
if body_text == "":
    send_email_not_found()
    print "No Documents found today!"
else:
    send_email_found(body_text)
    print "Found following results:-"
    print body_text
