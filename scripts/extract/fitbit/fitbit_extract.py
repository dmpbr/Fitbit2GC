import fitbit
import gather_keys_oauth2 as Oauth2
import pandas as pd 
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import os, sys
import data_vars

SET_ACCESS_TOKEN = data_vars.SET_ACCESS_TOKEN
SET_REFRESH_TOKEN = data_vars.SET_REFRESH_TOKEN
CLIENT_ID = data_vars.CLIENT_ID
CLIENT_SECRET = data_vars.CLIENT_SECRET
CALL_BACK= data_vars.CALL_BACK

weights_directory = os.path.join(os.path.expanduser('~'), 'Fitbit2GC', 'scripts', 'load', 'weights')


def getOauthClient(c_id, c_secret, oauth_call_back):
  try:
    ACCESS_TOKEN = SET_ACCESS_TOKEN
    REFRESH_TOKEN = SET_REFRESH_TOKEN
    auth2_client = fitbit.Fitbit(c_id, c_secret, oauth2=True, access_token=ACCESS_TOKEN, refresh_token=REFRESH_TOKEN, system=None)
  except BaseException as e:
    print("Got exception: {}".format(str(e)))
    server = Oauth2.OAuth2Server(client_id=c_id, client_secret=c_secret, redirect_uri=oauth_call_back)
    server.browser_authorize()
    ACCESS_TOKEN = str(server.fitbit.client.session.token['access_token'])
    REFRESH_TOKEN = str(server.fitbit.client.session.token['refresh_token'])
    auth2_client = fitbit.Fitbit(c_id, c_secret, oauth2=True, access_token=ACCESS_TOKEN, refresh_token=REFRESH_TOKEN, system=None)
  return auth2_client


def getWeightDataRange(fitbit_client, period_start_date='today', user_id=None, period_end_date=None):
  weight = fitbit_client.get_bodyweight(base_date=period_start_date, end_date=period_end_date)
  return weight



def getWeightGoal(fitbit_client):
  weight_goal = fitbit_client.body_weight_goal()
  print("Got weight goal: {}".format(weight_goal))
  return weight_goal



def getWeightAllData(fitbit_client, start_range=datetime.strptime('2015-01-01', '%Y-%m-%d'), end_range=datetime.today(), user_id= None):
  goal = getWeightGoal(fitbit_client)
  weight_array=[]

  if end_range < start_range:
    raise ValueError("Invalid date range. End Range {} earlier than Start Range {}".format(end_range, start_range))

  while start_range <= end_range:
    next_range = start_range + relativedelta(months=+1)
    if next_range > end_range:
      next_range = end_range
    weights = getWeightDataRange(fitbit_client, period_start_date=start_range.strftime('%Y-%m-%d'), period_end_date=next_range.strftime('%Y-%m-%d'))
    print("Got weights: {}".format(weights))
    if weights is not None and len(weights['weight'])>0:
      weight_array.append(weights)
    start_range+= relativedelta(months=+1)

  return (goal, weight_array)



def convertWeightArraytoDataframe(weight_goal, weight_data, dataframe_columns=['goal', 'logId', 'weight', 'time', 'bmi', 'date', 'source', 'fat']):
  wdf = pd.DataFrame(columns=dataframe_columns)
  logid_array = []
  weight_array = []
  time_array = []
  bmi_array = []
  date_array = []
  source_array = []
  fat_array = []
  for weight_period in weight_data:
    if 'weight' in weight_period.keys():
      for weight_measurement in weight_period['weight']:
        logid_array.append(weight_measurement['logId'] if 'logId' in weight_measurement.keys() else -1)
        weight_array.append(weight_measurement['weight'] if 'weight' in weight_measurement.keys() else -1)
        time_array.append(weight_measurement['time'] if 'time' in weight_measurement.keys() else '')
        bmi_array.append(weight_measurement['bmi'] if 'bmi' in weight_measurement.keys() else -1)
        date_array.append(weight_measurement['date'] if 'date' in weight_measurement.keys() else '')
        source_array.append(weight_measurement['source'] if 'source' in weight_measurement.keys() else 'Manual')
        fat_array.append(weight_measurement['fat'] if 'fat' in weight_measurement.keys() else -1)
  wdf['logId'] = logid_array
  wdf['weight'] = weight_array
  wdf['time'] = time_array
  wdf['bmi'] = bmi_array
  wdf['date'] = date_array
  wdf['source'] = source_array
  wdf['fat'] = fat_array

  if 'goal' in weight_goal.keys():
    wdf['goal'] = weight_goal['goal']['weight']
  return wdf


def writeDataframeToFile(dataframe, directory,filename):
  write_to = os.path.join(directory, filename)
  dataframe.to_csv(write_to, index_label='df_idx', encoding='utf-8')


def loadWeightsDataframeFromFile(directory, filename):
  in_dir = os.path.join(directory, filename)
  df = pd.read_csv(in_dir, index_col='df_idx')
  return df



if __name__ == "__main__":
  fbit = getOauthClient(c_id=CLIENT_ID, c_secret=CLIENT_SECRET, oauth_call_back=CALL_BACK)
  #(weight_goal, weight_data) = getWeightAllData(fbit)
  #print("The weight goal is: {} and we've received {} weights".format(weight_goal, len(weight_data)))
  #df = convertWeightArraytoDataframe(weight_goal, weight_data)
  #writeDataframeToFile(df, weights_directory, 'historical_weights.csv')
  df = loadWeightsDataframeFromFile(weights_directory, 'historical_weights.csv')
  print(df)
  
  

