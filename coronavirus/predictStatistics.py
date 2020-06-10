#python3 steven 
#LSTM regression, solve data set with time change
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
from tensorflow.keras import optimizers
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense,LSTM,BatchNormalization,TimeDistributed,Dropout
from sklearn.preprocessing import MinMaxScaler,StandardScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split, cross_val_score

from plotCoronavirous import binaryDf

gScaler = MinMaxScaler() #StandardScaler() #

gSaveBasePath=r'.\images\\'

def plotDataSet(data):
    plt.plot(data)
    plt.show()
    
def preprocessDb(dataset):
    dataset = gScaler.fit_transform(dataset)
    print('dataset=',dataset[:5])
    return dataset

# convert an array of values into a dataset matrix
def create_dataset(dataset, look_back=1):
    dataset = dataset.flatten()
    #print(dataset.shape)
    dataX, dataY = [], []
    for i in range(len(dataset)-look_back):
        a = dataset[i:(i+look_back)]
        dataX.append(a)
        dataY.append(dataset[i + look_back])
    return np.array(dataX), np.array(dataY)

def getDataSet():
    dataset = pd.read_csv('total-cases-covid-19.csv')
    dataset = dataset[dataset['Entity'] == 'World' ]
    dataset = dataset.rename(columns={"Total confirmed cases of COVID-19 (cases)": "Cases"})
    print(dataset.head())
    dataset = dataset.iloc[:, [2,3]]
    #dataset = dataset['Date', 'Cases']
    
    #print(dataset.describe().T)
    print(dataset.head())
    print(dataset.tail())
    print(dataset.shape)
    print(dataset.dtypes)
    return dataset

def plotData(ax,x,y,label=''):
    fontsize = 5
    ax.plot(x,y,label=label)
    #ax.set_aspect(1)
    ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right",fontsize=fontsize,fontweight=10)
    plt.setp(ax.get_yticklabels(), fontsize=fontsize)
    plt.subplots_adjust(left=0.02, bottom=0.09, right=0.99, top=0.92, wspace=None, hspace=None)

def predictFutuer(model,start,Number=5):
    print('---------------future')
    print(start)    
    #print(start.shape,'startval:', gScaler.inverse_transform(start.reshape(1,-1)))
    start = np.array([start]).reshape(1,1,1)
    result = []
    result.append(start.flatten()[0])
    for i in range(Number):
        next = model.predict(start)
        #print(next)
        result.append(next.flatten()[0])
        start = next
    print('predict value=',result)
    result = gScaler.inverse_transform(np.array(result).reshape(1,-1)).flatten()
    result = list(map(int, result))
    print('after inverse redict value=',result)
    return result

def plotPredictCompare(model,trainX,index,data):
    trainPredict = model.predict(trainX).flatten()
    trainPredict = gScaler.inverse_transform(trainPredict.reshape((trainPredict.shape[0],1))).flatten()
    
    data = data.flatten()
    #print(index.shape)
    #print(trainPredict.shape)    
    #print(data.shape)
    #print('raw=',data)
    #print('pred=',trainPredict)

    offset=70 #120
    plt.figure(figsize=(12,10))
    ax = plt.subplot(1,1,1)
    plotData(ax,index[offset+2:-1],data[offset+2:-1],'rawData')
    plotData(ax,index[offset+2:-1],trainPredict[offset+1:-1],'predict')
    plt.savefig(gSaveBasePath + 'WorldPredictCompare.png')
    plt.show()
 
def plotPredictFuture(model,trainY,index,data):
    Number = 10 #predict future Number days
    pred = predictFutuer(model,trainY[-1],Number)
    print('predict start date:',index[-1])

    startIndex = index[-1]
    sD=datetime.datetime.strptime(startIndex,'%b %d, %Y')
    newIndex=[]
    newIndex.append(startIndex)
    for i in range(Number):
        d = sD + datetime.timedelta(days=i+1)
        d = datetime.datetime.strftime(d,'%b %d, %Y')
        #print(d)
        newIndex.append(d)
    print('predict period:',newIndex)
    
    df = pd.DataFrame({'Date':newIndex,'Predicted cases':pred})
    print('table:',df)
    
    offset=70 #120
    plt.figure(figsize=(8,6))
    plt.title('Future Covid19 ' + str(Number) + ' days prediction')
    ax = plt.subplot(1,1,1)
    plotData(ax,index[offset:],data[offset:],'now cases')
    plotData(ax,newIndex,pred,'predict cases')
    ax.table(cellText=df.values, colLabels=df.columns, loc='center') #,clip_box=[[0,5],[0+100,5+100]]
    plt.savefig(gSaveBasePath + 'WorldFuturePredict.png')
    plt.show()
    
def createModel(look_back = 1):
    model = Sequential()
    #model.add(BatchNormalization(input_shape=(1, look_back)))
    #model.add(LSTM(100, input_shape=(1, look_back)))
    model.add(LSTM(100,input_shape=(1, look_back), activation='relu', return_sequences=True))
    #model.add(LSTM(80, activation='relu', return_sequences=True))
    #model.add(LSTM(50, activation='relu', return_sequences=True))
    #model.add(BatchNormalization())
    model.add(TimeDistributed(Dense(30, activation='relu')))
    model.add(Dense(20,activation='relu'))
    model.add(Dense(10,activation='relu'))
    model.add(Dense(1))
    
    lr = 0.001
    #opt = optimizers.SGD(learning_rate=lr) #optimizers.SGD(learning_rate=lr, momentum=0.8, nesterov=False)
    opt = optimizers.Adam(learning_rate=lr)
    #opt = optimizers.RMSprop(learning_rate=lr, rho=0.9, epsilon=1e-08)
    model.compile(optimizer=opt, loss='mean_squared_error')  #optimizer='adam'
    model.summary()
    return model

def train(dataset):
    index = dataset.iloc[:,0].values
    rawdata = dataset.iloc[:,1].values    
    rawdata = rawdata.reshape((rawdata.shape[0],1))
    #print('raw=',rawdata[-5:])
    data = preprocessDb(rawdata) #scaler features
    #print('raw=',rawdata[-5:])
    #print('index=',index[-5:])

    look_back = 1
    trainX, trainY = create_dataset(data, look_back) 
   
    print('x=\n',trainX[-5:])
    print('y=\n',trainY[-5:])
    print('trainX.shape = ',trainX.shape)
    print('trainY.shape = ',trainY.shape)
    trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
    #print('trainX.shape = ',trainX.shape)

    model = createModel(look_back)
    model.fit(trainX, trainY, epochs=100, batch_size=50, verbose=2) #500
    
    # a = np.array([trainY[-1]]).reshape(-1,1,1)
    # #a = np.array([[0.88964097]]).reshape(-1,1,1)
    # #a = np.array([0.6]).reshape(1,1,1)
    # print(a)
    # print('predict=', model.predict(a))

    #-----------------start plot---------------#
    plotPredictCompare(model,trainX,index,rawdata)
    plotPredictFuture(model,trainY,index,rawdata)
       
def predict():
    dataset = getDataSet()
    train(dataset)
    
def main():
    predict()
    
if __name__=='__main__':
    main()