#!/usr/bin/env python
# coding: utf-8

# In[87]:


import logging.config
from datetime import datetime
log = logging.getLogger('named_entitiy_extractor')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s] (%(funcName)s:%(lineno)d) > %(message)s')
fh = logging.FileHandler('./{:%Y-%m-%d_%H-%M}.log'.format(datetime.now()))
fh.setFormatter(formatter)
log.addHandler(fh)


# In[88]:


import os
import sys
import glob
import json

ele_school_list = []
mid_school_list = []
high_school_list = []
etc_school_list= []


#Result of this program
counts = dict()


# In[89]:


# Reference source : (한국교육학술정보원 2020년 기준 전국초중고 학교 리스트) https://www.schoolinfo.go.kr/ng/go/pnnggo_a01_l0.do 
# https://m.blog.naver.com/edisondl/221975906950

def load_reference():

    global ele_school_list
    global mid_school_list
    global high_school_list
    global etc_school_list

    log.debug('-------------------- Load reference files --------------------\n')
    input_path = "./data/SCHOOL_CODE/JSON/"
    
    file_counter = 0
    for input_file in glob.glob(os.path.join(input_path, 'schoolList_2020_*')):
        with open(input_file, 'r') as json_file:
            data = json.load(json_file)
            data_list = data['list']
            tmp_list = []    
             #학교별 메타(주소,이름)정보 리스트 생성
            school_name = data_list[0]['SCHUL_NM']
            if "초등학교" in school_name:      
                ele_school_list = tmp_list
            elif "중학교" in school_name:
                mid_school_list = tmp_list
            elif "고등학교" in school_name:
                high_school_list = tmp_list
            else:
                etc_school_list += tmp_list

            #필요한 항목만 메모리에 적재
            for row in data_list:
                a_row = {}
                a_row["SCHOOL_ADDR"]= row['ADRES_BRKDN']
                a_row["SCHOOL_NAME"]= row['SCHUL_NM']
                tmp_list.append(a_row)

            log.debug('Loaded {0:d} rows '.format(len(tmp_list)))
        log.debug('{0!s}\n'.format( os.path.basename(input_file)))
        file_counter += 1
    log.debug('{0:d} files are loaded.'.format(file_counter))


# In[90]:


def get_reference_list(region, name):
    if "예술" in name:
        return etc_school_list
    elif "초등학교" in name or "초" in name[-1:]:  
        return ele_school_list
    elif "중학교" in name or "중" in name[-1:]:
        return mid_school_list
    elif "고등학교" in name or "고" in name[-1:]:
        return high_school_list
    else:
        return None


# In[91]:


def print_final_result():
    lst = list()
    comment_count=0
    f = open("./result/result.txt", "w")
    for key, val in list(counts.items()):
        comment_count += val
        lst.append((val, key))

    lst.sort(reverse=True)
    for item in lst :
        str = "%s\\t%d\n"%( item[1], item[0])
        f.write(str)
    
    f.close()    
    log.debug("########")
    log.debug(" * Number of processed comments: %d , extracted school counts: %d"% ( comment_count, len(counts)))
    log.debug(counts)


# In[92]:


def add_final_result(result):
    if (result == None): return
    sc_name = result[0]['SCHOOL_NAME']
    
    log.debug("Add this as final result ==> %s"%sc_name)
    try: 
        counts[sc_name] +=1
        
    except KeyError:
        counts[sc_name] = 1    


# In[93]:


"""Reference data에 있는 학교이름 리스트를 생성

   Args:
     school_name: A str of school_name
     data_list: ele, mid, high school list based on school_name selected loaded on memory

   Returns:
     school_list: list of school metadata(ADDRESS, NAME) 
"""
   
def get_school_list_from_refer(school_name, data_list):
   log.debug("make_school_info")
   school_list = []    
   for i in data_list:
       try:
           if school_name in i['SCHOOL_NAME']:
               school_list.append(i)
           
       except IndexError as ie :
           log.error(ie)
           return None
       except Exception as e:
           log.error(e)
   return school_list


# In[94]:


"""region을 이용한 Reference data에 있는 학교이름 리스트를 생성

   Args:
     region: A list of assumed region words which extracted from regex
     school_name: A str of school_name
     data_list: ele, mid, high school list based on school_name selected loaded on memory

   Returns:
     school_list: list of school metadata(ADDRESS, NAME) 
"""
   
def get_school_list_with_region(region, school_name, data_list):
   if region == None or len(region) == 0 :
       return []
   
   school_list = []
   for i in data_list:
       try:
           if region[0] in i['SCHOOL_ADDR'] and school_name in i['SCHOOL_NAME']:
               school_list.clear()
               school_list.append(i)
               return school_list
       except IndexError as ie :
           log.error(ie)
           return None
       except Exception as e:
           log.error(e)
   
   


# In[95]:


def modify_acronate(name):
    """레퍼런스 검색을 위한 축약어 해제
    """   
    rs=name.find("여중")
    if rs > -1:
        return name[:rs]+"여자중"
    rs=name.find("여고")    
    if rs > -1:
        return name[:rs]+"여자고"
    rs=name.find("예중")
    if rs > -1:
        return name[:rs]+"예술중"
    rs=name.find("예고")
    if rs > -1:
        return name[:rs]+"예술고"
    rs=name.find("체고")
    if rs > -1:
        return name[:rs]+"체육고"
    else :
        return name


# In[96]:


def revise_refer_result(region, school_name, data_list):
    '''후보 학교리스트 1개로 줄이기
       Args:
           data_list: 1reference 를 참조하여 검색된 학교의 리스트 중 동음으로 된 학교가 있는 경우, 모든 같은이름 list
           region
           school_name
        
       Returns:
           학교이름(school_name) 앞에 명시한 지역이름 (ex:성남은행중학교)를 참조하여 학교리스트를 1개로 줄인다.
       
    '''
    if data_list != None and len(data_list) == 0:
        school_list=[]
        region = school_name[:2]
        school_name = school_name[-3:]
        for i in data_list:
            province_name = i['SCHOOL_ADDR']
            if school_name in i['SCHOOL_NAME'] and region in province_name:
                school_list=[]
                school_list.append(i)
                return school_list
            elif school_name in i['SCHOOL_NAME']:
                 school_list.append(i)
        return school_list


# In[97]:


def get_valid_school_name(region, sc_name):
    """학교이름 업데이트
       1) regex에서 제대로 school_name이 추출되지 않은 경우로,
        region에 학교 이름이 포함되어 있는 경우, 학교이름을 region을 기반으로 보정한다
        ex)  region:[용인, 영문중],  우리중 -->  school_name: 용인영문중
       
    """
    if region != None and region != [] :
        region[0] = region[0].replace("시", "")

    if ("우리" in sc_name or "저희" in sc_name or "다른" in sc_name or "사대부" in sc_name):
        _sc_name = "".join(region[:2])
        log.debug("Renamed school name %s -> %s"%(sc_name, _sc_name))
        sc_name = modify_acronate(_sc_name)
        return sc_name
    if sc_name == "중학교" or sc_name=="고등학교" or sc_name=="여자고등학교":
        return ""
    return sc_name


# In[98]:


def extract_name_only(sc_name):
    #~~시 에서 '시'제거
    if len(sc_name) > 3:
        sc_name = sc_name.replace("시","") if sc_name[2]=='시' else sc_name
    
    #~학교, ~고 , ~중으로 끝나는 경우에만 추가
    if (sc_name[-1:]=='고' or sc_name[-1:]=='중' or sc_name[-1:]=='대'):
        return sc_name
    
    _index= sc_name[:10].find("학교")
    sc_name = sc_name[:_index+2]
    
    return sc_name
    


# In[99]:


def remove_prefix_region_recursive(sc_name, reference_list):
    sc_name=extract_name_only(sc_name)
    log.debug("to remove prefix: %s" % sc_name)
    
    """학교이름 지역명 분리
        학교이름 앞에 지역이름이 있는 경우 reference에서 찾지 못하는경우
        school_name에서 지역region을 분리.
        
        학교명에 지역이름이 포함되는 경우일 경우 2자씩 끊어가며 reference에서 찾는다.
        - ex: 대구정화중학교 -> region:['대구'], sc_name: 정화중학교
        - ex: 인천서구서곶중학교 -> region:['인천'], sc_name: 서구서곶중학교
         -> region:['인천', '서구'], sc_name:서곶중학교
    """
    if reference_list==None:
        log.debug("reference list is null")
    revise_result=None
    while revise_result == None and len(sc_name)>0:
        log.debug("---- revise School name based on region from %s"%sc_name)
        region = []
        region.append(sc_name[:2])
        sc_name = sc_name[2:]
        revise_result = get_school_list_with_region(region, sc_name, reference_list)
        log.debug(revise_result)        
    return revise_result


# In[ ]:





# In[100]:


def select_one_on_multi_regions(region, school_list, school_name=""):
    """
        동일학교명이 여러지역에 있을경우 regex에서 추출한 지역명(region)과 reference의 학교주소로 비교
    """

    result_list = []
    for i in school_list:
        sc_name = i['SCHOOL_NAME']
        if school_name == sc_name:
            result_list.append(i)
            return result_list
    for i in school_list:
        province_name1 = i['SCHOOL_ADDR'].split(" ")[0]
        province_name2 = i['SCHOOL_ADDR']
        if province_name1 in " ".join(region):
            result_list.append(i)
            return result_list
        elif len(region) > 0:
            for r in region:
                if r in province_name2: #동탄푸른중
                    result_list.append(i)
                    return result_list


# In[101]:


def make_dict_withouth_address(sc_name):
    res = dict()
    res['SCHOOL_NAME'] = sc_name
    list = []
    list.append(res)
    return list


# In[102]:


"""
    Arguments:
        regex_result: 앞 단계에서 실행했던 정규식 결과셋
        text: Comment 본문
        need_update_school_name: 학교명이 축약어(예술중 False 예중 True) 여부
    Returns: 
        - list of school meta information(dict)
        - None

"""

def process_read_refer(regex_result, text, need_update_school_name = False):
    if regex_result == None:
        text ="".join(text)
        regex1 = r"([가-힣]+)학교"
        regex_result = re.search(regex1, text)
        if regex_result == None : return None       
    
    
    start_index = regex_result.span()[0]
    #!같은 학교이름이 여러지역에 있을 경우
    sc_name = modify_acronate(regex_result.group()) if need_update_school_name==True else regex_result.group() 
    
    region = re.compile('[가-힣]+').findall(text[0:start_index])
    sc_name = get_valid_school_name(region, sc_name)
    log.debug("==Regex result==,region: %s, school_name: %s"%(region, sc_name))
  
    
    if len(region)>10:
        region = []

    reference_list=[]
    reference_list = get_reference_list(region, sc_name)
    #대학교
    if reference_list is None : 
        #add_this_school_without_reference
        return make_dict_withouth_address(sc_name)
    revise_result = get_school_list_from_refer(sc_name, reference_list)
    log.debug(revise_result)
    
    len_result = 0
    if revise_result != None: len_result =len(revise_result)
    if len_result == 1:
        log.debug(revise_result)
        log.debug("------- Extraced info 1")
        return revise_result        
        
    elif len_result > 1:
        log.debug("len result %d"%len_result)
        #후보 학교 리스트가 여러개일 경우, region리스트와 실 주소를 참조하여 1개로 줄인다
        revise_result = select_one_on_multi_regions(region, revise_result, sc_name)
        if revise_result != None and len(revise_result)==1:
            log.debug("----- Extract info 2")
            log.debug(revise_result)
            return revise_result
        else: 
            log.debug("----- Extract info 3")
            res = revise_refer_result(region, sc_name, revise_result)
            log.debug(res)
            if res != None and len(res)==1:
                return res
    else:#region리스트가 비어있을 때, 학교이름에 명시된 지역명으로 찾는다.
        revise_result = remove_prefix_region_recursive(sc_name, reference_list)
        if revise_result == None :
            log.debug("FAILED %s"% sc_name)
            return make_dict_withouth_address(extract_name_only(sc_name))
        else:
            return revise_result
    


# In[103]:


def data_loader(file_path):
    """
        Args:file_path of input csv file
        Returns: <class '_csv.reader'>
    """
    csv_file = open(file_path, newline='')
    input_reader = csv.reader(csv_file, quotechar='"', delimiter=',', 
                              quoting=csv.QUOTE_ALL, skipinitialspace=True, escapechar='\\')
    return input_reader


# In[104]:



import re
import csv
def extract_school_info(input_reader):
    """
        Args: cvs reader
                
    """
    log.debug('---------------- Let\'s start to extract school name entity ----------------\n')
    index = 0

    for comment in input_reader:
        index = index + 1
        text = comment[0]

        log.debug("\n======== %d ========\n%s"%(index, text))

        regex1 = r"([가-힣]+)학교"
        result_search = re.search(regex1, text)
        if result_search is not None:
            log.debug("===== ROUND 1 ====")
            res = process_read_refer(result_search, text)
            add_final_result(res)     
        else:
            log.debug("===== ROUND 2 ====")
            regex2 = r"([가-힣]+)[초|중|고|대]"
            result_search = re.search(regex2, text)
            res = process_read_refer(result_search, text, True)
            add_final_result(res)
 
    print_final_result()
    fh.close()


# In[ ]:





# In[105]:


def main():
    log.debug("================== KaKao Bank 2021 Named-entity Recognition =====================")
    load_reference()
    data_reader = data_loader('./data/comments.csv')  
    
    extract_school_info(data_reader)
    print("Created logs on current foler.")
    print("result on ./result/resutl.txt")
if __name__ == "__main__":
    main()

main()


# In[106]:


import unittest

class reviseTest(unittest.TestCase):
    
    def test_remove_prefix_region_recursive1(self):
        sc_name = "인천서구서곶중학교"
        reference_list = mid_school_list
        c = remove_prefix_region_recursive(sc_name, reference_list)
        print(c)
        self.assertEqual(len(c), 1)
        self.assertEqual(c[0]['SCHOOL_ADDR'].split(" ")[0], "인천광역시")
        self.assertEqual(c[0]['SCHOOL_NAME'], "서곶중학교")
        
        sc_name = "서구서곶중학교"
        reference_list = mid_school_list
        c = remove_prefix_region_recursive(sc_name, reference_list)
        print(c)
        self.assertEqual(len(c), 1)
        self.assertEqual(c[0]['SCHOOL_ADDR'].split(" ")[0], "인천광역시")
        self.assertEqual(c[0]['SCHOOL_NAME'], "서곶중학교")
        
    def test_remove_prefix_region_recursive2(self):
        sc_name="부산양덕여자중학교"
        reference_list = mid_school_list
        c = remove_prefix_region_recursive(sc_name, reference_list)
        print(c)
        self.assertEqual(len(c), 1)
        self.assertEqual(c[0]['SCHOOL_ADDR'].split(" ")[0], "부산광역시")
        self.assertEqual(c[0]['SCHOOL_NAME'], "양덕여자중학교")
            
    def test_remove_prefix_region_recursive3(self):
        sc_name = "서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교"
        reference_list = mid_school_list
        c = remove_prefix_region_recursive(sc_name, reference_list)
        print(c)
        self.assertEqual(len(c), 1)
        self.assertEqual(c[0]['SCHOOL_ADDR'].split(" ")[0], "서울특별시")
        self.assertEqual(c[0]['SCHOOL_NAME'], "장평중학교")
    
        
    def text_extract_name_only(self):
        sc_name = "서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교서울장평중학교"
        c = extract_name_only(sc_name)
        self.assertEqual(c, "서울장평중학교")
    def text_extract_name_only2(self):
        sc_name = "고양시행신중"
        c = extract_name_only(sc_name)
        self.assertEqual(c, "고양행신중")
        
        
    def test_select_one_on_multi_regions(self):
        reference_data = "[{\"SCHOOL_ADDR\": \"서울특별시 서대문구 홍은동\", \"SCHOOL_NAME\": \"명지중학교\"},         {\"SCHOOL_ADDR\": \"부산광역시 강서구 명지동 \", \"SCHOOL_NAME\": \"명지중학교\"}, {\"SCHOOL_ADDR\": \"충청남도 서산시 대산읍\", \"SCHOOL_NAME\": \"서산명지중학교\"}]"
        ref_school_list= json.loads(reference_data)
        
        region = ['도시', '냄새가', '풍기는', '서울', '산과', '어우러져', '있는'] 
        c = select_one_on_multi_regions(region, ref_school_list, "")
        print(c)

        sc_name = "명지중학교"
        self.assertEqual(len(c), 1)
        self.assertEqual(c[0]['SCHOOL_ADDR'].split(" ")[0], "서울특별시")
        self.assertEqual(c[0]['SCHOOL_NAME'], sc_name)
        
    def test_select_one_on_multi_regions2(self):

        reference_data =  "[{\"SCHOOL_ADDR\": \"울산광역시 남구 무거동 \", \"SCHOOL_NAME\": \"삼호중학교\"},                             {\"SCHOOL_ADDR\": \"전라남도 영암군 삼호읍 용앙리\", \"SCHOOL_NAME\": \"삼호중학교\"}]"
        ref_school_list = json.loads(reference_data)
        
        region = ['전라남도', '영암군', '삼호읍', '방아제로']
        
        c = select_one_on_multi_regions(region, ref_school_list, "")
        print(c)
        self.assertEqual(len(c), 1)
        self.assertEqual(c[0]["SCHOOL_ADDR"].split(" ")[0], "전라남도")
        
    def test_select_one_on_multi_regions3(self):
        reference_data = "[{\"SCHOOL_ADDR\": \"경기도 이천시 장호원읍 노탑리\", \"SCHOOL_NAME\": \"장호원고등학교\"},             {\"SCHOOL_ADDR\": \"경기도 의정부시 호원동\", \"SCHOOL_NAME\": \"호원고등학교\"}]"
        region =  ['경기도', '의정부시', '호원동'] 
        sc_name = "호원고등학교"
        
        ref_school_list= json.loads(reference_data)
        c = select_one_on_multi_regions(region, ref_school_list, sc_name)
        print(c)
        self.assertEqual(len(c),1)
        self.assertEqual(c[0]["SCHOOL_ADDR"].split(" ")[0], "경기도")
        
    def test_get_valid_school_name(self):
        region = ['용인' ,'영문중']
        sc_name = "우리중"
        c = get_valid_school_name(region, sc_name)
        self.assertEqual(c, "용인영문중")  
    def test_get_valid_school_name2(self):
        region = ['고양시' ,'행신중']
        sc_name = "저희학교"
        c = get_valid_school_name(region, sc_name)
        self.assertEqual(c, "고양행신중")  
    
    def test_modify_acronate(self):
        n="서울세화여중"
        c=modify_acronate(n)
        self.assertEqual(c, "서울세화여자중")
        
        n="세화여중"
        c=modify_acronate(n)
        self.assertEqual(c,"세화여자중")
                          
        n="세화여고"
        c=modify_acronate(n)
        self.assertEqual(c, "세화여자고")
        
        n="인천체고"
        c=modify_acronate(n)
        self.assertEqual(c, "인천체육고")
        
        n="선화예중"
        c=modify_acronate(n)
        self.assertEqual(c, "선화예술중")

        n="선화예고"
        c=modify_acronate(n)
        self.assertEqual(c, "선화예술고")


if __name__ == '__main__':
    print("Start unit test.")
    load_reference()
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


# In[ ]:





# In[ ]:




