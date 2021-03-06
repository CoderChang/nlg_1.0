#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: YuMS
# @Date:   2014-07-16 16:47:47
# @Last Modified by:   YuMS
# @Last Modified time: 2014-07-22 14:50:11

from flask import Flask, request, jsonify, current_app
from functools import wraps
from nlg import nlg
import json,time

app = Flask(__name__)
sessions = {}

def jsonp(func):
    """Wraps JSONified output for JSONP requests."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            data = str(func(*args, **kwargs).data)
            content = str(callback) + '(' + data + ')'
            mimetype = 'application/javascript'
            return current_app.response_class(content, mimetype=mimetype)
        else:
            return func(*args, **kwargs)
    return decorated_function

@app.route("/", methods=['GET', 'POST'])
@jsonp
def index():
  this_input = json.loads(request.args['data'])
  #print sessions.keys()
  if "session-id" in this_input:
    if this_input["end-flag"] == 0:
      output = {}
      output["session-id"] = this_input["session-id"]
      output["domain"] = this_input["domain"]
      output["end-flag"] = this_input["end-flag"]
      output["module-name"] = "NLG"
      output["timestamp"] = time.time()
      output["log"] = "Null"
      if this_input["session-id"] not in sessions:
	sessions[this_input["session-id"]] = nlg()
      tar = sessions[this_input["session-id"]]
      output["content"] = tar.interface(this_input["content"])
      #output["content"],output["log"] = nlg.json2nlg(this_input["data"]["dialog−acts"],"inform")
      return jsonify(**output)
    else:
      if this_input["session-id"] in sessions:
	del sessions[this_input["session-id"]]
      else:
	pass
      output = {}
      output["session-id"] = this_input["session-id"]
      output["domain"] = this_input["domain"]
      output["end-flag"] = this_input["end-flag"]
      output["module-name"] = "NLG"
      output["timestamp"] = time.time()
      output["log"] = "Null"
      output["content"] = {}
      return jsonify(**output)
  else:
    return jsonify(**nlg().interface(this_input))
    
    
    #if "session" in dm_output.keys():
        #turn_id = dm_output["data"]["turn-id"]
        #if turn_id == 0:
            #dic[dm["session"]] = nlg("../nlg.cfg")
        #tar = dic[dm["session"]]
        #return jsonify(**nlg.json2nlg(dm_output["data"]["dialog−acts"],"inform")) #第二参数有问题，“inform”仅为其中一种情况，cl学长说暂时先这样吧
    #else:
        #tar = nlg("../nlg.cfg")
        #return jsonify(**nlg.json2nlg(dm_output["dialog−acts"],"inform"))
if __name__ == "__main__":
    app.debug = True
    # app.run()
    app.run(host='0.0.0.0', port=4924)
                              
