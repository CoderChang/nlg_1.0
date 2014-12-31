# coding:UTF-8

import codecs
import os
# sys.path.append(os.path.dirname(__file__))
# import action
# import dm
import string
# import dmmodel
import json


class nlg_action_template:
    def __init__(self):
        self.act = ""
        self.order = 0  # the order of act
        self.tgt1 = ""
        self.slot1 = {}
        self.tgt2 = ""
        self.slot2 = {}
        self.pattern = {}


class sys_master_nlg_action(object):
    """docstring for sys_master_nlg_action"""
    def __init__(self):
        self.act = ""
        self.order = -1
        self.tgt1 = ""
        self.tgt2 = ""
        self.slot1 = {}
        self.slot2 = {}
        self.nlgtgt1 = ""
        self.nlgtgt2 = ""
        self.nlgslot1 = {}
        self.nlgslot2 = {}


class nlg_model:
    def __init__(self):
        self.actionlist = {}


class nlg(object):
    def __init__(self, nlg_cfg_dir="../nlg.cfg"):
        nlg_res_dir = self.input_nlg_cfg(nlg_cfg_dir)
        self.nlg_res = self.input_nlg_res(nlg_res_dir)

    def interface(self, dm_output):
        sys_summary_action = None
        sys_master_action = None
        if "summary-action" in dm_output:
            sys_summary_action = dm_output["summary-action"]
        if "dialog-acts" in dm_output:
            sys_master_action = dm_output["dialog-acts"]
        nlg_txt_list = self.json2nlg(sys_master_action, sys_summary_action)
        nlg_txt = ""
        for txt in nlg_txt_list:
            if len(nlg_txt) > 0:
                nlg_txt += "\n"
            nlg_txt += txt
        nlg_output = {}
        nlg_output["nlg-txt"] = nlg_txt
        nlg_output["nlg-display"] = ""
        return nlg_output

    def input_nlg_cfg(self, nlg_cfg_dir):
        nlg_res_dir = {}
        file_handle = codecs.open(nlg_cfg_dir, "r", "utf-8")
        file_list = file_handle.readlines()
        for file_line in file_list:
            file_line = file_line.lower()
            file_line = file_line.replace("\t", "")
            file_line = file_line.replace(" ", "")
            file_line = file_line.replace("\n", "")
            if file_line.startswith('#') is True or len(file_line) == 0:
                continue
            file_line = file_line.split('#')[0]
            file_line = file_line.split('=')
            if len(file_line) == 1:
                continue
            nlg_res_dir[file_line[0]] = (os.path.split(os.path.realpath(__file__))[0] + "/" + file_line[1])

        return nlg_res_dir

    def input_nlg_res(self, nlg_res_dir):
        nlg_res = {}
        if 'ontology' in nlg_res_dir:
            ontology_file = file(nlg_res_dir['ontology'])
            nlg_res["ontology"] = json.load(ontology_file)
            nlg_res["chn_eng"] = self.map_chn_eng(nlg_res["ontology"])
            nlg_res['slot_map_islot'] = self.slot2islot(nlg_res["ontology"])
        if 'nlg.res.en' in nlg_res_dir:
            nlg_res['nlg_model'] = load_nlgmodel(nlg_res_dir['nlg.res.en'],
                                                 nlg_res['chn_eng'])

        return nlg_res

    def map_chn_eng(self, ontology):
        chn_eng = {}
        chn_map_eng = {}
        eng_map_chn = {}
        # ########## processe ontology
        for concept in ontology:
            eng_map_chn[ontology[concept]['eng_name']] = \
                ontology[concept]['chn_name']
            chn_map_eng[ontology[concept]['chn_name']] = \
                ontology[concept]['eng_name']

        chn_eng['chn_map_eng'] = chn_map_eng
        chn_eng['eng_map_chn'] = eng_map_chn

        return chn_eng

    def slot2islot(self, ontology):
        slot_map_islot = {}

        for concept in ontology:
            if ontology[concept]['ntype'] == "islot":
                for son in ontology[concept]["sons"]:
                    slot_map_islot[son] = concept

        return slot_map_islot

    def json2nlg(self, sys_master_action_list, sys_summary_action):
        for i, action in enumerate(sys_master_action_list):
            act_type = action['act']
            slot_value_pair = action['slots']
            if act_type != "offer" and len(action['slots']) == 2:
                sys_master_action_list[i]['slots'][1] = unicode(action['slots'][1])
            elif act_type == "offer":
                entity = action['slots'][1]
                if entity is not None:
                    for slot in entity:
                        sys_master_action_list[i]['slots'][1][slot] = unicode(entity[slot])

        chn_eng = self.nlg_res['chn_eng']
        slot_map_islot = self.nlg_res['slot_map_islot']
        nlgmodel = self.nlg_res['nlg_model']

        nlg_txt_list = []

        nlg_txt = ""
        nlg = sys_master_nlg_action()

        if len(sys_master_action_list) == 0:
            nlg_txt = u"我可以用对话的方式为您查找团购。"
            nlg_txt_list.append(nlg_txt)
            return nlg_txt_list

        # ####### querymore
        if sys_summary_action == "querymore":
            nlg.act = "querymore"
            nlg.nlgtgt1 = "operation"
            nlg.order = 1
            nlg_txt = nl_gen(nlg,nlgmodel,"max")
            nlg_txt_list.append(nlg_txt)

        # ####### select
        if sys_summary_action == "select":
            # for sys_master_action in sys_master_action_list:
            nlg = sys_master_nlg_action()           
            nlg.act = sys_summary_action
            nlg.order = 1
            # for action in sys_master_action:
            nlg.nlgtgt1 = "all"
            value1 = sys_master_action_list[0]['slots'][1]
            value2 = sys_master_action_list[1]['slots'][1]          
            nlg.nlgslot1["all"] = (u"你是喜欢%s，还是喜欢%s" %(value1,value2))
            nlg_txt = nl_gen(nlg, nlgmodel, "max")
            nlg_txt_list.append(nlg_txt)
        if sys_summary_action == "userconfirm":
            for action in sys_master_action_list:
                act_type = action['act']
                if act_type in ["affirm", "negate"]:
                    sys_summary_action = act_type
                    break

        # ####### affirm
        if sys_summary_action == "affirm":
            nlg = sys_master_nlg_action()
            nlg.act = sys_summary_action
            nlg.order = 0
            nlg_txt = nl_gen(nlg, nlgmodel, "max")
            nlg_txt_list.append(nlg_txt)

        # ###### negate
        if sys_summary_action == "negate":
            # for sys_master_action in sys_master_action_list:
            nlg = sys_master_nlg_action()
            nlg.act = sys_summary_action
            nlg.order = 1
            for action in sys_master_action_list:
                act_type = action['act']
                slot_value_pair = action['slots']
                nlg.nlgtgt1 = "all"
                if "all" not in nlg.nlgslot1:
                    nlg.nlgslot1["all"] = ""
                chn_name = chn_eng['eng_map_chn'][slot_value_pair[0]]
                nlg.nlgslot1["all"] += (chn_name + u"是" + slot_value_pair[1])
            nlg_txt = nl_gen(nlg, nlgmodel, "max")
            nlg_txt_list.append(nlg_txt)

        # ###### split
        if sys_summary_action == "split":
            nlg.act = "split"
            nlg.order = 1
            # for sys_master_action in sys_master_action_list:
            for action in sys_master_action_list:
                act_type = action['act']
                slot_value_pair = action['slots']
                # for slot_value in slot_value_pairs:
                nlg.nlgtgt1 = slot_map_islot[slot_value_pair[0]]
                nlg.nlgslot1[slot_value_pair[0]] = slot_value_pair[1]
            nlg_txt = nl_gen(nlg, nlgmodel, "max")
            nlg_txt_list.append(nlg_txt)

        # ####### inform
        if sys_summary_action == "inform":
            sys_master_action_list = inform2list(sys_master_action_list)
            for sys_master_action in sys_master_action_list:
                nlg = sys_master_nlg_action()
                nlg.act = "inform"
                nlg.order = 1
                for action in sys_master_action:
                    # print action,sys_master_action_list
                    act_type = action['act']
                    slot_value_pair = action['slots']
                    nlg.nlgtgt1 = "name"
                    if slot_value_pair[0] == "name":
                        if "name" not in nlg.nlgslot1:
                            nlg.nlgslot1["name"] = ""
                        nlg.nlgslot1["name"] = slot_value_pair[1] + nlg.nlgslot1["name"]
                    else:
                        if "name" not in nlg.nlgslot1:
                            nlg.nlgslot1["name"] = ""
                        chn_name = chn_eng['eng_map_chn'][slot_value_pair[0]]
                        nlg.nlgslot1["name"] += (chn_name + u"是" + slot_value_pair[1])
                nlg_txt = nl_gen(nlg,nlgmodel,"max")
                nlg_txt_list.append(nlg_txt)

        # ####### other
        if sys_summary_action in ["hello","askrepeat","restart","hangup","backchn","ok","thanks","recomplain","unsupport","confrestart","rehelp","bye"]:
            nlg = sys_master_nlg_action()       
            nlg.act = sys_summary_action
            nlg.order = 0
            nlg_txt = nl_gen(nlg,nlgmodel,"max")
            nlg_txt_list.append(nlg_txt)

        # ###### confirm
        if sys_summary_action == "confirm":
            #for sys_master_action in sys_master_action_list:
            nlg = sys_master_nlg_action()           
            nlg.act = sys_summary_action
            nlg.order = 1
            for action in sys_master_action_list:
                act_type = action['act']
                slot_value_pair = action['slots']
                nlg.nlgtgt1 = "all"
                if "all" not in nlg.nlgslot1:
                    nlg.nlgslot1["all"] = ""
                chn_name = chn_eng['eng_map_chn'][slot_value_pair[0]]
                nlg.nlgslot1["all"] += (chn_name + u"是" + slot_value_pair[1])
            nlg_txt = nl_gen(nlg, nlgmodel, "max")
            nlg_txt_list.append(nlg_txt)

        # ####### confreq
        if sys_summary_action == "confreq":
            #for sys_master_action in sys_master_action_list:
            nlg = sys_master_nlg_action()           
            nlg.act = sys_summary_action
            nlg.order = 2
            if len(sys_master_action_list) == 2:
                for action in sys_master_action_list:
                    act_type = action['act']
                    slot_value_pair = action['slots']
                    if act_type == "confirm":
                        nlg.nlgtgt1 = slot_value_pair[0]
                        nlg.nlgslot1[slot_value_pair[0]] = slot_value_pair[1]
                    elif act_type == "request":
                        nlg.nlgtgt2 = slot_value_pair[1]
                nlg_txt = nl_gen(nlg,nlgmodel,"max")
                nlg_txt_list.append(nlg_txt)    

        ######## request
        if sys_summary_action == "request":
            nlg.act = sys_summary_action
            nlg.nlgtgt1 = sys_master_action_list[0]["slots"][1]
            nlg.order = 1
            nlg_txt = nl_gen(nlg,nlgmodel,"max")
            nlg_txt_list.append(nlg_txt)

        ######## offer
        if sys_summary_action in ["offer","offerconf","offerselect","offerreq","offeralt"]:
            offer_none_flag = False
            #if sys_summary_action == "offer":
            for action in sys_master_action_list:
                act_type = action['act']
                slot_value_pair = action['slots']
                if act_type == "offer" and slot_value_pair[1] == None:
                    nlg_txt = u"抱歉，未找到符合您要求的团购。"
                    offer_none_flag = True
                    break
            if offer_none_flag == False:
                nlg_txt = u"帮您找到以下团购。"
            if sys_summary_action in ["offerconf","offerselect","offerreq","offeralt"]:
                nlg = sys_master_nlg_action()           
                nlg.order = 1
                select_value1 = None
                select_value2 = None
                for action in sys_master_action_list:
                    act_type = action['act']
                    slot_value_pair = action['slots']
                    ##### offerreq
                    if act_type == "request":
                        nlg.act = "request"
                        nlg.nlgtgt1 = slot_value_pair[1]
                        #nlg_txt += nl_gen(nlg,nlgmodel,"max")
                    ##### offerconf
                    elif act_type == "confirm":     
                        nlg.act = "confirm"
                        nlg.nlgtgt1 = "all"
                        if "all" not in nlg.nlgslot1:
                            nlg.nlgslot1["all"] = ""
                        chn_name = chn_eng['eng_map_chn'][slot_value_pair[0]]
                        nlg.nlgslot1["all"] += (chn_name + u"是" + slot_value_pair[1])
                    elif act_type == "select":
                        nlg.act = "select"
                        nlg.nlgtgt1 = "all"
                        if select_value1 == None:
                            select_value1 = slot_value_pair[1]
                        elif select_value2 == None:
                            select_value2 = slot_value_pair[1]
                        if select_value1 != None and select_value2 != None:         
                            nlg.nlgslot1["all"] = (u"你是喜欢%s，还是喜欢%s" %(select_value1,select_value2))                     
                nlg_txt += nl_gen(nlg,nlgmodel,"max")
            nlg_txt_list.append(nlg_txt)
            for i,action in enumerate(sys_master_action_list):
                act_type = action['act']
                slot_value_pair = action['slots']               
                if offer_none_flag == False and act_type == "offer":
                    nlg_txt = ""
                    #for action in sys_master_action:
                    entity = slot_value_pair[1]
                    for slot in entity:
                        if slot == "name":
                            nlg_txt = (u"\t电影:" + entity[slot] + "\t") + nlg_txt
                        else:
                            chn_name = chn_eng['eng_map_chn'][slot]
                            nlg_txt += ("\t" + chn_name + u":" + entity[slot])
                    nlg_txt_list.append(nlg_txt)

        return nlg_txt_list


def inform2list(sys_inform_action):
    sys_inform_action_list = []
    temp_action = []
    inform_slots = []
    for i, action in enumerate(sys_inform_action):
        slots = action['slots']
        if len(slots) > 0:
            slot = slots[0]
            if slot not in inform_slots:
                inform_slots.append(slot)
                temp_action.append(action)
            else:
                sys_inform_action_list.append(temp_action)
                temp_action = []
                temp_action.append(action)
                inform_slots = []
                inform_slots.append(slot)
    if len(temp_action) > 0:
        sys_inform_action_list.append(temp_action)

    # print sys_inform_action_list

    return sys_inform_action_list


def isnumber(string0):
    string1 = string0.replace(".", "", 1)
    if(string1.isdigit()):
        return True
    else:
        return False


def load_nlgmodel(nlgfile, chn_eng):
    nlgmodel = nlg_model()
    chn_map_eng = chn_eng['chn_map_eng']
    # print json.dumps(chn_map_eng,indent=4,ensure_ascii=False)
    eng_map_chn = chn_eng['eng_map_chn']
    eng_map_chn["all"] = "all" # support all slot
    # print json.dumps(eng_map_chn,indent=4,ensure_ascii=False)
    dmm_handle = codecs.open(nlgfile, "r", "utf-8")
    file_list = dmm_handle.readlines()
    txton = 0
    linenum = 0
    for file_line in file_list:
        linenum += 1
        file_line = file_line
        file_line = file_line.replace("\t\t", "\t")
        file_line = file_line.replace("\t\t", "\t ")
        file_line = file_line.replace("\t", " ")
        file_line = file_line.replace("  ", " ")
        file_line = file_line.replace("  ", " ")
        file_line = file_line.replace("\n", "")
        file_line = file_line.replace("\"", "")
        if(not file_line.startswith("#") and len(file_line) > 0
                and not file_line.isspace()):
            # print ""
            # print file_line, txton
            if(file_line.startswith("MA:")):    # get action and parameters
                file_line = file_line.strip("MA: ")
                file_line = file_line.strip("MA:\t")
                file_line = file_line.strip("\t")
                file_line = file_line.replace(" ", "")
                file_line = file_line.lower()
                seglist = file_line.split("(")
                if(len(seglist) >= 2):
                    # print seglist
                    debug = True
                    if debug:
                        # if(seglist[0] in machine_ms_action_dict):
                        act = seglist[0]
                        nlgaction = nlg_action_template()
                        nlgaction.act = act
                        # print act
                        if(act not in nlgmodel.actionlist):
                            nlgmodel.actionlist[act] = []
                        nlgmodel.actionlist[act].append(nlgaction)
                        rmd = seglist[1]
                        rmd = rmd.strip(")")
                        # print act, rmd
                        if(len(rmd) > 0):
                            rmdlist = rmd.split(";")
                            # for tgt1 and slot1
                            rmdlist1 = rmdlist[0].split(",")
                            # print rmdlist1
                            for each in rmdlist1:
                                if(each.startswith("__tgt1__=")):

                                    tgtlist = each.split("=")[1].split("::")
                                    tgtnorm = ""
                                    allin = 1
                                    for tgt in tgtlist:
                                        if((not tgt in eng_map_chn) and (not tgt in chn_map_eng)):
                                            allin=0;
                                            break;
                                        elif(tgt in eng_map_chn):
                                            tgtnorm=tgtnorm+"::"+tgt
                                        elif(tgt in chn_map_eng):
                                            tgtnorm=tgtnorm+"::"+chn_map_eng[tgt]                                       
                                    if(allin==1):
                                        nlgaction.tgt1=tgtnorm[2:]
                                    else: 
                                        print "NLG MODEl ERROR: line: %s, machine action: __tgt1__ value %s is not defined in ontology file" %(linenum,tgt)
                            
                                elif(each.startswith("slot1=")): #parse slot1
                                    slotlist=each.split("=")[1].split("::")
                                    for slot in slotlist:
                                        if(slot in eng_map_chn):
                                            nlgaction.slot1[slot]=1
                                        elif(slot in chn_map_eng):
                                            nlgaction.slot1[chn_map_eng[slot]]=1
                                        elif(slot == "db_status"):
                                            nlgaction.slot1["db_status"]=1
                                        elif(slot == "unsupported"):
                                            nlgaction.slot1["unsupported"]=1
                                        else:
                                            print "NLG MODEl ERROR: line: %s, machine action: slot1 %s is not defined in ontology file" %(linenum,slot)
                                
                                    # print nlgaction.slot1                                     
                            # for tgt2 and slot2
                            if(len(rmdlist)>1):
                                rmdlist2=rmdlist[1].split(",")
                                for each in rmdlist2:
                                    if(each.startswith("__tgt2__=")): #parse tgt2
                                        tgtlist=each.split("=")[1].split("::")
                                        tgtnorm="";
                                        allin=1;
                                        for tgt in tgtlist:
                                            if((not tgt in eng_map_chn) and (not tgt in chn_map_eng)):
                                                allin=0;
                                                break;
                                            elif(tgt in eng_map_chn):
                                                tgtnorm=tgtnorm+"::"+tgt
                                            elif(tgt in chn_map_eng):
                                                tgtnorm=tgtnorm+"::"+chn_map_eng[tgt]                                           
                                        if(allin==1):
                                            nlgaction.tgt2=tgtnorm[2:]
                                        else: 
                                            print "NLG MODEl ERROR: line: %s, machine action: __tgt2__ value %s is not defined in ontology file" %(linenum,tgt)
                                    
                                        # print "zhou", nlgaction.tgt2                                  
                                    elif(each.startswith("slot2=")):  #parse slot2
                                        slotlist=each.split("=")[1].split("::")
                                        for slot in slotlist:
                                            if(slot in eng_map_chn):
                                                nlgaction.slot2[slot] = 1
                                            elif(slot in chn_map_eng):
                                                nlgaction.slot2[chn_map_eng[slot]]=1
                                            elif(slot == "db_status"):
                                                nlgaction.slot2["db_status"] = 1
                                            elif(slot == "unsupported"):
                                                nlgaction.slot2["unsupported"] = 1
                                            else:
                                                print "NLG MODEL ERROR: line: %s, machine action: slot2 %s is not defined in ontology file" %(linenum, slot)
                                        
                    else:
                        print "NLG MODEL ERROR: line: %s, machine act: %s is not defined in action file" %(linenum,act)
                                    
                else:
                    print "NLG MODEL ERROR: line: %s, machine action: %s is invalid" %(linenum,file_line)
                
                    
            elif(file_line.startswith("{")):    #nlg pattern begin          
                txton=1;
            elif(file_line.startswith("}")):    #nlg pattern end 
                txton=0;
            elif(txton==1):                 #nlg pattern
                linelist=file_line.split(" ")
                if(len(linelist)>1):
                    if(isnumber(linelist[1])):
                        prob=string.atof(linelist[1])
                    else:
                        print "NLG MODEL ERROR: line %s, txt probability %s is invalid" %(linenum,linelist[1])                                                  
                else:
                    prob=1;
                # check if all slot in action's parameter list 
                slotlist = linelist[0].split("[")
                allin=1;
                for slot in slotlist:
                    endindex=slot.find("]")
                    if(endindex>0):
                        slotname=slot[:endindex]
                        if(slotname in eng_map_chn and (slotname in nlgaction.slot1 or slotname in nlgaction.slot2)):
                            continue
                        elif(slotname in chn_map_eng and (chn_map_eng[slotname] in nlgaction.slot1 or chn_map_eng[slotname] in nlgaction.slot2)):
                            continue
                        elif(slotname=="db_status" and (slotname in nlgaction.slot1 or slotname in nlgaction.slot2)):
                            continue
                        elif(slotname=="unsupported" and (slotname in nlgaction.slot1 or slotname in nlgaction.slot2)):
                            continue
                        else:
                            allin = 0
                            print "NLG MODEL ERROR: line: %s, slot: %s is not in the nlg action parameter list" %(linenum,slotname)
                            
                if(allin==1):
                    nlgaction.pattern[linelist[0]]=prob
            
    return nlgmodel

def disp_nlgmodel(nlgmodel):
    for act in nlgmodel.actionlist:
        for actnlg in nlgmodel.actionlist[act]:
            actstr= act + "(__tgt1__=" + actnlg.tgt1 +",slot1="
            for slot in actnlg.slot1:
                if(actstr[-1]=="="):
                    actstr = actstr + slot
                else:
                    actstr = actstr + "::" + slot
            actstr = actstr + ";"
            actstr= actstr + "__tgt2__=" + actnlg.tgt2 +",slot2="
            for slot in actnlg.slot2:
                if(actstr[-1]=="="):
                    actstr = actstr + slot
                else:
                    actstr = actstr + "::" + slot
            actstr = actstr + ")"
            print actstr
            print "{"
            for nlgtxt in actnlg.pattern:
                print "%s %5.2f" %(nlgtxt,actnlg.pattern[nlgtxt])
            print "}"
    return 0


def tgtmatch(tgt1, tgt2): # check tgt1==tgt2
    tgt1list=tgt1.split("::")
    tgt2list=tgt2.split("::")
    allin1=0;
    for t1 in tgt1list:
        if(t1 in tgt2list):
            allin1+=1;
    if(allin1==len(tgt1list)):
        allin2=0
        for t2 in tgt2list:
            if(t2 in tgt1list):
                allin2+=1
    if(allin1==len(tgt1list) and allin2==len(tgt2list)):
        return 1
    else:
        return 0


def slotmatch(slotlist1,slotlist2): #check slot1==slot2
    allin1=0;
    for slot1 in slotlist1:
        if(slot1 in slotlist2):
            allin1+=1;
    if(allin1==len(slotlist1)):
        allin2=0
        for slot2 in slotlist2:
            if(slot2 in slotlist1):
                allin2+=1
    if(allin1==len(slotlist1) and allin2==len(slotlist2)):
        return 1
    else:
        return 0
        


def nl_gen(machine_ms_action, nlgmodel, means):
    
    nlg_txt = ""
    act=machine_ms_action.act
    #print act;
    #print nlgmodel.actionlist
    #if(act=="repeat"):
    #   nlg_txt=ptree.nlg_txt
    if(act in nlgmodel.actionlist):
        # find matched nlg pattern
        
        for actnlg in nlgmodel.actionlist[act]:
            matchall=0
            if(machine_ms_action.order==0): #for order=0
                matchall=1
            if(machine_ms_action.order>=1): #for order=1
                # print machine_ms_action.tgt1
                # print actnlg.tgt1
                # print machine_ms_action.slot1
                # print actnlg.slot1
                matchtgt1=tgtmatch(machine_ms_action.nlgtgt1,actnlg.tgt1)   
                matchslot1=slotmatch(machine_ms_action.nlgslot1,actnlg.slot1)
                if(matchtgt1==1 and matchslot1==1):
                    matchall=1  
            if(machine_ms_action.order==2 and matchall==1): #for order=2    
                # print machine_ms_action.tgt2
                # print actnlg.tgt2
                # print machine_ms_action.slot2
                # print actnlg.slot2
                matchtgt2=tgtmatch(machine_ms_action.nlgtgt2,actnlg.tgt2)   
                matchslot2=slotmatch(machine_ms_action.nlgslot2,actnlg.slot2)               
                if(machine_ms_action.order==2 and matchtgt2==1 and matchslot2==1):
                    matchall=1
                else:
                    matchall=0
            if(matchall==1):
                break;
        
        if(matchall==1): #for matched
            if(means=="random"):
                accprob=[]
                txtlist=[]
                accprob.append(0)       
                for txt in actnlg.pattern:                      
                    txtlist.append(txt)
                    accprob.append(accprob[len(accprob)-1]+actnlg.pattern[txt])
                nlg_txt=txtlist[dm.random_select(accprob)]
            elif(means=="max"):
                maxprob=-1
                maxtxt=""
                for txt in actnlg.pattern:
                    if(maxprob<actnlg.pattern[txt]):
                        maxprob=actnlg.pattern[txt]
                        maxtxt=txt
                nlg_txt=maxtxt
                    
            else:
                maxprob=-1;
                maxtxt=""
                for txt in actnlg.pattern:
                    if(maxprob<actnlg.pattern[txt]):
                        maxprob=actnlg.pattern[txt]
                        maxtxt=txt
                nlg_txt=maxtxt
            # print "zhou"
            startindex=nlg_txt.find("[")            
            while (startindex>=0):
                
                endindex=nlg_txt.find("]")
                # print startindex,endindex
                slotname=nlg_txt[startindex+1:endindex]
                # print slotname
                # print machine_ms_action.slot1[slotname]
                if(slotname in machine_ms_action.nlgslot1):
                    # print "zhou1"
                    nlg_txt=nlg_txt.replace(nlg_txt[startindex:endindex+1],machine_ms_action.nlgslot1[slotname])
                elif(slotname in machine_ms_action.nlgslot2):
                    # print "zhou2"
                    nlg_txt=nlg_txt.replace(nlg_txt[startindex:endindex+1],machine_ms_action.nlgslot2[slotname])
                else:
                    debug = 1
                    print "NLG ERROR: slot %s in nlg model has no slot value in machine_ms_action" %(slotname)
                # print nlg_txt             
                startindex=nlg_txt.find("[")
                
        else: #for no matched 
            #print "NLG ERROR: there is no nlg pattern match the machine_ms_action: %s" %(action.nlgaction2json(machine_ms_action)) 
            debug = 2
            # print "NLG ERROR: there is no nlg pattern match the machine_ms_action:"     
    else: #for no act matched
        debug = 3
        # print "NLG ERROR: act %s is not defined in nlg model file" %(act)
        
    
    return nlg_txt


if __name__ == "__main__":
    nlg = nlg("../nlg.cfg")
    # nlg_res = nlg.nlg_res
    # disp_nlgmodel(nlg_res['nlg_model'])

    sys_summary_action = "offer"
    sys_master_action = [
        {
            "slots": [
                "entity", None
            ],
            "act":"offer",
        },
        {
            "slots":[
                "entity",{
                    "name":"jjjjjj2",
                    "actor":"zhangsan"
                }
            ],
            "act":"offer",
        },
        {
            "slots":[
                "director","director",
            ],
            "act":"confirm",            
        },  
        {
            "slots":[
                "actor","director",
            ],
            "act":"confirm",            
        },
    ]

    dm_output = {}
    dm_output["summary-action"] = sys_summary_action
    dm_output["dialog-acts"] = sys_master_action
    nlg_output = nlg.interface(dm_output)
    print nlg_output["nlg-txt"]