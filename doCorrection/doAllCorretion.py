from subprocess import call
import multiprocessing
import sys
from array import array
from ROOT import *

sys.path.append('./lambdas_singleCB')

def GetLambda(isData, pTRange, etaRange, fs, iteration):

    lambdaFileName = 'pT_' + str(float(pTRange[0])) + '_' + str(float(pTRange[1])) + '_eta_' + str(float(etaRange[0])) + '_' + str(float(etaRange[1]))
    lambdaFileName = lambdaFileName.replace('.','p')
    if isData:
       lambdaFileName += '_'+fs+'_data'
    else:
       lambdaFileName += '_'+fs+'_mc'

    tmpLambda =  __import__(lambdaFileName, globals(), locals())
    lambdas = tmpLambda.lambdas
 
    with open('lambdas_singleCB/'+lambdaFileName+'_log.txt', 'a')  as f:
         f.write('iteration ' + str(iteration) + ': ' + str(lambdas)+'\n')

    lambdas_tagged = ['pT_' + str(float(pTRange[0])) + '_' + str(float(pTRange[1])) + '_eta_' + str(float(etaRange[0])) + '_' + str(float(etaRange[1])), lambdas]
   
    return lambdas_tagged



def doLambda1(pTRange, etaRange, inpath, outpath, fs, isData):

    cmd  = ' python doCorrection.py \
             --ptLow ' + str(pTRange[0]) + ' --ptHigh ' + str(pTRange[1]) \
         + ' --etaLow '  + str(etaRange[0]) + ' --etaHigh ' + str(etaRange[1]) \
         + ' --ptLow_lambda1 ' + str(pTRange[0]) + ' --ptHigh_lambda1 ' + str(pTRange[1]) \
         + ' --etaLow_lambda1 '  + str(etaRange[0]) + ' --etaHigh_lambda1 ' + str(etaRange[1]) \
         + ' --fs ' + fs + ' --doLambda1 --doPara --lambdas 1 1 ' \
         + ' --inpath ' + inpath + ' --outpath ' + outpath + ';'

    cmd += ' python doCorrection.py \
             --ptLow ' + str(pTRange[0]) + ' --ptHigh ' + str(pTRange[1]) \
         + ' --etaLow '  + str(etaRange[0]) + ' --etaHigh ' + str(etaRange[1]) \
         + ' --ptLow_lambda1 ' + str(pTRange[0]) + ' --ptHigh_lambda1 ' + str(pTRange[1]) \
         + ' --etaLow_lambda1 '  + str(etaRange[0]) + ' --etaHigh_lambda1 ' + str(etaRange[1]) \
         + ' --fs ' + fs + ' --doLambda1 --lambdas 1 1 ' \
         + ' --inpath ' + inpath + ' --outpath ' + outpath 

    call(cmd, shell=True)

    lambdas = GetLambda(isData, pTRange, etaRange, fs, 0)

    return lambdas




def doLambda2(pTRange, etaRange, inpath, outpath, fs, isData, lambda1Info, iterationMax):

    lambda1_pt = lambda1Info[0]
    lambda1_eta = lambda1Info[1]
    lambda1 = lambdaInfo[2]

    cmd = ' python doCorrection.py \
            --ptLow ' + str(pTRange[0]) + ' --ptHigh ' + str(pTRange[1]) \
        + ' --etaLow '  + str(etaRange[0]) + ' --etaHigh ' + str(etaRange[1]) \
        + ' --ptLow_lambda1 ' + str(lambda1_pt[0]) + ' --ptHigh_lambda1 ' + str(lambda1_pt[1]) \
        + ' --etaLow_lambda1 '  + str(lambda1_eta[0]) + ' --etaHigh_lambda1 ' + str(lambda1_eta[1]) \
        + ' --fs ' + fs + ' --doPara --lambdas ' + str(lambda1) + ' 1 ' \
        + ' --inpath ' + inpath + ' --outpath ' + outpath + ';'

    cmd+= ' python doCorrection.py \
            --ptLow ' + str(pTRange[0]) + ' --ptHigh ' + str(pTRange[1]) \
        + ' --etaLow '  + str(etaRange[0]) + ' --etaHigh ' + str(etaRange[1]) \
        + ' --ptLow_lambda1 ' + str(lambda1_pt[0]) + ' --ptHigh_lambda1 ' + str(lambda1_pt[1]) \
        + ' --etaLow_lambda1 '  + str(lambda1_eta[0]) + ' --etaHigh_lambda1 ' + str(lambda1_eta[1]) \
        + ' --fs ' + fs + ' --lambdas ' + str(lambda1) + ' 1 ' \
        + ' --inpath ' + inpath + ' --outpath ' + outpath

    needMoreCorrection = True
    iteration = 0
    lambdas = GetLambda(isData, pTRange, etaRange, fs, iteration)
    lambdas['lambda2'] *= lambdas['lambda']

    if (lambdas['lambda2'] - 1) < 0.1:
       return lambdas

    while (needMoreCorrection):

          iteration += 1
          lambda2 = lambdas['lambda2']
         
          cmd = ' python doCorrection.py \
                  --ptLow ' + str(pTRange[0]) + ' --ptHigh ' + str(pTRange[1]) \
              + ' --etaLow '  + str(etaRange[0]) + ' --etaHigh ' + str(etaRange[1]) \
              + ' --ptLow_lambda1 ' + str(lambda1_pt[0]) + ' --ptHigh_lambda1 ' + str(lambda1_pt[1]) \
              + ' --etaLow_lambda1 '  + str(lambda1_eta[0]) + ' --etaHigh_lambda1 ' + str(lambda1_eta[1]) \
              + ' --fs ' + fs + ' --lambdas ' + str(lambda1) + ' ' + str(lambda2) \
              + ' --inpath ' + inpath + ' --outpath ' + outpath 

          call(cmd, shell=True)          
          lambdas = GetLambda(isData, pTRange, etaRange, fs, iteration)
          lambdas['lambda2'] *= lambdas['lambda']

          if (lambdas['lambda'] - 1) < 0.1 or iteration == iterationMax:
             needMoreCorrection = False

    return lambdas


def MakeLUT(pTs, etas, allLambdas, isData, fs, outpath):
    #make LUT of corrections
    binPt, binEta = array('f'), array('f')
    for i in range(len(pTs)): binPt.append(pTs[i])
    for i in range(len(etas)): binEta.append(etas[i])

    LUT = TH2F("2"+fs, "", len(binPt)-1, binPt, len(binEta)-1, binEta)
    for i in range(len(binPt)-1):
        for j in range(len(binEta)-1):
            tag = 'pT_' + str(float(pTs[i])) + '_' + str(float(pTs[i+1])) + '_eta_' + str(float(etas[j])) + '_' + str(float(etas[j+1]))
            for k in range(len(allLambdas)):
                if allLambdas[k][0] == tag:
                   LUT.SetBinContent(i+1,j+1, allLambdas[k][1]['lambda'])

    if isData:
       file1 = "DoubleLepton_m2"+fs+"LUT_m2"+fs+".root"
    else:
       file1 = "DYJetsToLL_M-50_m2"+fs+"LUT_m2"+fs+".root"

    c1 = TCanvas("c1","",800,800)
    LUT.Draw("text")
    c1.SaveAs(outpath+"LUT_"+fs+".png")

    f1 = TFile('lambdas_singleCB/'+file1, "RECREATE")
    f1.cd()

    LUT.Write()
    f1.Close()

def doMuon(muonPt, muonEta, inpath, outpath, isData):

    pool = multiprocessing.Pool( len(muonEta) -1 )
    tasks = []

    #split jobs into different process
    for i in range(len(muonEta)-1):
        tasks.append( (muonPt, [muonEta[i],muonEta[i+1]], inpath, outpath, 'mu', isData) )

    results = [pool.apply_async( doLambda1, t ) for t in tasks]
   
    allLambdas = []
    for result in results:
        (lambdas) = result.get()
        allLambdas.append(lambdas)
        print lambdas

    MakeLUT(muonPt, muonEta, allLambdas, isData, 'mu', outpath)

def doElectron(electronPt, electronEta, inpath, outpath, isData):

    lambda1 = doLambda1([7,100], [0,0.8], inpath, outpath, 'e', isData)

    pool = multiprocessing.Pool( (len(electronEta) -1)*(len(electronPt) - 1) )
    tasks = []

    #split jobs into different process
    for i in range(len(electronPt)-1):
        for j in range(len(electronEta)-1):
            tasks.append( ([electronPt[i], electronPt[i+1]], [electronEta[j], electronEta[j+1]], inpath, outpath, 'e', isData, \
                           [[7,100],[0,0.8],lambda1[1]['lambda']], 5) )

    results = [pool.apply_async( doLambda2, t ) for t in tasks]

    allLambdas = []
    for result in results:
        (lambdas) = result.get()
        allLambdas.append(lambdas)
        print lambdas

    MakeLUT(electronPt, electronEta, allLambdas, isData, 'e', outpath)



inpath = '/raid/raid9/mhl/HZZ4L_Run2_post2016ICHEP/outputRoot/DY_2015MC_kalman_v4_NOmassZCut_useLepFSRForMassZ/'
outpath = '/home/mhl/public_html/2016/20161125_mass/test/'

muonPt = [5,100]
muonEta = [0, 0.9, 1.8, 2.4]

electronPt = [7,100]
electronEta = [0,0.8,1.5,2,2.5]

#doMuon(muonPt, muonEta, inpath, outpath, False)
doElectron(electronPt, electronEta, inpath, outpath, False)
### define lambda1 binning in doElectron
