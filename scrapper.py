from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_recaptcha_solver import RecaptchaSolver
from selenium.webdriver.chrome.service import Service
from fp.fp import FreeProxy
import time
import pandas as pd


def launch_browser():
#        proxy = FreeProxy().get()

        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')  # run without GUI
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")
#        options.add_argument(f'--proxy-server={proxy}')
        
        print("Starting driver")
        service = Service("/usr/local/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        print("Driver Started")

        driver = webdriver.Chrome(service=service, options=options)
        return driver



def scrape_result(driver, roll_number, dob, output):

    try:
        driver.get("https://erp.aktu.ac.in/webpages/oneview/oneview.aspx")

        # Wait for Roll Number field and enter roll number
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'txtRollNo')))
        print("Successful get to website")
            
        roll = driver.find_element(By.ID, 'txtRollNo')
        roll.clear()
        roll.send_keys(roll_number)
        driver.find_element(By.ID, 'btnProceed').click()


        # wait for page to load
        time.sleep(2)

        # Wait for Roll Number field and enter roll number
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'txtDOB')))
        roll = driver.find_element(By.ID, 'txtRollNo')
        roll.clear()
        roll.send_keys(roll_number)


        # Enter DOB
        dob_field = driver.find_element(By.ID, 'txtDOB')
        dob_field.clear()
        dob_field.send_keys(dob)

        # Solve reCAPTCHA
        try:
            recaptcha_iframe = driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')
            solver = RecaptchaSolver(driver)
            solver.click_recaptcha_v2(iframe=recaptcha_iframe)
        except Exception as e:
            pass

        # Submit the form
        driver.find_element(By.ID, 'btnSearch').click()

        # Wait for the result to appear
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'pnlContent')))

        roll_no = driver.find_element(By.ID, "lblRollNo").text
        full_name = driver.find_element(By.ID, "lblFullName").text
        branch_name = driver.find_element(By.ID, "lblBranch").text

        print(full_name, roll_no)
        time.sleep(2)

        accordians = driver.find_elements(By.XPATH, "//div[contains(@id, 'accordion')]")

        for accordian in accordians:
            driver.execute_script("arguments[0].scrollIntoView(true);", accordian)
            time.sleep(2)
            accordian.click()

        semIdElements = driver.find_elements(By.XPATH, "//*[contains(@id, 'lblSemesterId') and not(contains(@id, 'for'))]")
        reqSemId = 7

        for elem in semIdElements:
            semId = int(elem.text)

            if(semId == reqSemId):
                parent_table_element = elem.find_element(By.XPATH, './ancestor::table[1]')
                SGPA = parent_table_element.find_element(By.XPATH, './/*[contains(@id, "lblSGPA")]').text
                subjects = parent_table_element.find_elements(By.XPATH, './/table[contains(@id, "grdViewSubjectMarksheet")]/tbody/tr')
                subjects.pop(0)

                total = 0

                for subject in subjects:
                    values = subject.find_elements(By.XPATH, './td')

                    subject_code = values[0].text
                    subject_name = values[1].text
                    internal_marks = int(values[3].text.strip()) if values[3].text.strip() != "" else 0
                    external_marks = int(values[4].text.strip()) if values[4].text.strip() != "" else 0
                    total_marks = internal_marks + external_marks
                    grade = values[6].text

                    if(len(output['Name']) == 0):
                        output[subject_name + "_internal"] = []
                        output[subject_name + "_external"] = []
                        output[subject_name + "_total"] = []
                        output[subject_name + "_grade"] = []
                    
                    output[subject_name + "_internal"].append(internal_marks)
                    output[subject_name + "_external"].append(external_marks)
                    output[subject_name + "_total"].append(total_marks)
                    output[subject_name + "_grade"].append(grade)
                    
                    total += total_marks

                    # print(subject_name, internal_marks, external_marks, total_marks, grade)
                output["Name"].append(full_name)
                output["RollNo"].append(roll_no)
                output["total"].append(total)
                output["SGPA"].append(SGPA)

                print(output)

    except Exception as e:
        return f"<pre>Error: {str(e)}</pre>"



def excel_data():
    df = pd.read_excel("./data.xlsx")
    df[df.columns[7]] = df[df.columns[7]].dt.strftime("%d/%m/%Y") 
    df = df[[df.columns[1], df.columns[7]]]
    # selected_rows = df.iloc[297:352]
    # for testing purpose only extracting 3 rows
    selected_rows = df.iloc[297:300]
    return selected_rows.values.tolist()



# 🔽 Add this block to run when file is executed directly
if __name__ == "__main__":
    try:
        students = excel_data()
        driver = launch_browser()
        output = {"Name" : [], "RollNo": [], "total": [], "SGPA": []}

        for student in students:
            scrape_result(driver, student[0], student[1], output)

        output = pd.DataFrame(output)
        output.to_excel("output.xlsx", index=False)

    except Exception as e:
        print("Error", e)
    finally:
        driver.quit()
