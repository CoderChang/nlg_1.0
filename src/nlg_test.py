import nlg as NLG

if __name__=="__main__":
	nlg = NLG.nlg("../nlg.cfg")
	#nlg_res = nlg.nlg_res
	#disp_nlgmodel(nlg_res['nlg_model'])

	sys_summary_action = "offerselect"
	sys_master_action_list1 = [
		{
			"slots":[
				["name","none1"],
			],
			"act":"offer",
		},
		{
			"slots":[
				["actor","zhangsan"],
			],
			"act":"inform",
		},
		{
			"slots":[
				["name","The big bang2"],
			],
			"act":"offer",
		},
		{
			"slots":[
				["actor","zhangsan"],
			],
			"act":"inform",
		},
		{
			"slots":[
				["name","The big bang"],
				["name","The big bang2"],
			],
			"act":"select",
		}

	]

	sys_master_action_list2 = [
		{
			"slots":[
				["name","The big bang"],
			],
			"act":"negate",
		}
	]

	sys_master_action_list3 = [
		{
			"slots":[
				["name","The big bang"],
				["name","The big bang2"],
			],
			"act":"select",
		}
	]


	for sys_summary_action in ["offerselect"]:
		nlg_txt_list = nlg.json2nlg(sys_master_action_list3,sys_summary_action)

		for nlg_txt in nlg_txt_list:
			print nlg_txt