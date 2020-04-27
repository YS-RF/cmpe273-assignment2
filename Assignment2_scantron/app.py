from flask import Flask, escape, request
import sqlite3
import ast
import json
import pprint

app = Flask(__name__)
conn = sqlite3.connect("CMPE273DB.db")
c=conn.cursor()

c.execute(''' DROP TABLE IF EXISTS test_answer''')
c.execute('''CREATE TABLE test_answer(
            test_id INT PRIMARY KEY, subject TEXT, answer_keys BLOB)''')

c.execute(''' DROP TABLE IF EXISTS scantron''')
c.execute('''CREATE TABLE scantron(
            scantron_id INT, test_id REFERENCES test_answer(test_id),
            scantron_url TEXT, name TEXT, subject TEXT, score INT, result BLOB)''')

conn.commit()
conn.close()

test_id_globo = 0
scantron_id_globo = 0

@app.route('/')
def hello():
    name = request.args.get("name", "World")
    return f'Hello, {escape(name)}!'

@app.route('/api/tests', methods=['POST'])
def add_test():
    if request.method =='POST':
        conn = sqlite3.connect("CMPE273DB.db")
        c=conn.cursor()
        data = request.json

        global test_id_globo

        test_id = test_id_globo
        subject = data['subject']
        answer_keys = data['answer_keys']

        test_id_globo+=1

        c.execute('INSERT INTO test_answer VALUES(?,?,?)', (test_id,subject,str(answer_keys)))

        conn.commit()
        conn.close()
        return """test_id:{}\nsubject:{}\nanswer_keys:{}""".format(test_id,subject,answer_keys)
        

@app.route('/api/tests/<test_id>', methods=['GET'])
def check_submission(test_id):
    if request.method == 'GET':
        conn = sqlite3.connect("CMPE273DB.db")
        c=conn.cursor()
        inloop_int = 0
        c.execute('SELECT * FROM test_answer WHERE test_id = ?',test_id)

        answer_data = str(c.fetchone())
        answer_data = ast.literal_eval(answer_data)    
        
        return_json = {}
        return_json["test_id"] = answer_data[0]
        return_json["subject"] = answer_data[1]
        return_json["answer_keys"] = answer_data[2]

        return_json["submission"] = []

        c.execute('SELECT * FROM scantron WHERE test_id=?',test_id)

        submission_section = c.fetchall()

        for x in submission_section:
            return_json['submission'].append({})


            return_json['submission'][inloop_int]['scantron_id']=ast.literal_eval(str(x))[0]
            return_json['submission'][inloop_int]['scantron_url']=ast.literal_eval(str(x))[2]
            return_json['submission'][inloop_int]['name']=ast.literal_eval(str(x))[3]
            return_json['submission'][inloop_int]['subject']=ast.literal_eval(str(x))[4]
            return_json['submission'][inloop_int]['score']=ast.literal_eval(str(x))[5]
            return_json['submission'][inloop_int]['result']=ast.literal_eval(str(x))[6]
            inloop_int+=1



        conn.close()



        return return_json

        
@app.route('/api/tests/<test_id>/scantrons', methods=['POST'])
def submit_scantron(test_id):
    if request.method == 'POST':
        conn = sqlite3.connect("CMPE273DB.db")
        c=conn.cursor()
        #read answer
        c.execute('SELECT answer_keys FROM test_answer WHERE test_id = ?',test_id)
        answerString = str(c.fetchone())
        testAnswer = ast.literal_eval(answerString)
        testAnswer = ast.literal_eval(testAnswer[0])

        #parse scantron object
        score = 0
        global scantron_id_globo
        f = request.files['data']
        file = f.read()
        scantron = json.loads(file)
        scantron_url = "http://127.0.0.1:5000/files/scantron-"+str(scantron_id_globo)+".json"
        scantron_id = scantron_id_globo
        scantron_id_globo+=1
        name = scantron['name']
        subject = scantron['subject']
        scantronAnswer = scantron['answers']
        answer_add_to_scantron = {}

        for key in testAnswer:
            if (key in scantronAnswer):
                answer_add_to_scantron[key]={}
                answer_add_to_scantron[key]["actual"] = scantronAnswer[key]
                answer_add_to_scantron[key]["expected"] = testAnswer[key]
                
                if (testAnswer[key]==scantronAnswer[key]):
                    score+=1
        
        
        

        c.execute('''INSERT INTO scantron VALUES(?,?,?,?,?,?,?)''', 
                (scantron_id, test_id, scantron_url, name,subject, score, str(answer_add_to_scantron) ))

        conn.commit()
        conn.close()

        return '''scantron_id: {}\nscantron_url: {}
                name: {}\nscore: {}\nscantronAnswer: {}'''.format(scantron_id, 
                        scantron_url, name, score, json.dumps(answer_add_to_scantron,indent=4, sort_keys=True))





if __name__ =="__main__":
    app.run(debug=True)

    