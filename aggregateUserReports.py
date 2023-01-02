import os
import pickle
import pandas as pd

def main():
    allUserReports = getAllUserReports()
    allUserReports = removeAllIncompleteUserReports(allUserReports)
    results = getAllEligiblePiecesOfEvidence(allUserReports)
    generateReport(allUserReports, results[0], results[1], results[2])

# TODO: Do a much more efficient implementation (This would require changing the format of the user reports.)

# This function retrieves all of the user reports collected from end users.
# Here, I'm assuming that all user reports are in the ./data/user_reports directory
def getAllUserReports():
    allUserReports = []
    userReportsDirectory = os.getcwd() + "/data/user_reports/"
    print ("Getting all user reports saved in ", userReportsDirectory)
    for filename in os.listdir(userReportsDirectory):
        if not filename.startswith('.'):
            print (filename)
            f = pd.read_pickle(os.path.join(userReportsDirectory, filename))
            allUserReports.append(f)
    print(allUserReports)
    return allUserReports


# Remove all incomplete end user reports and do some clean up (like removing the array).
def removeAllIncompleteUserReports(allUserReports, printRaw = True):
    allCompleteUserReports = []
    rawData = []
    if printRaw:
        rawData = open(os.getcwd() + '/raw_user_reports.txt', 'w')
    for f in allUserReports:
        currReport = f[0] # We need to get to the JSON file without df
        if currReport['complete_status'] != True:
            print("Skipping an incomplete report")
            if printRaw:
                rawData.write('\n\nA Report NOT Going In:\n')
                rawData.write(str(currReport))
        else:
            print("Going to do something with this report")
            allCompleteUserReports.append(currReport)
            if printRaw:
                rawData.write('\n\nAnother Report Going In:\n')
                rawData.write(str(currReport))
    return allCompleteUserReports

def getTranslatedVerdict(systemDeci, judgement):
    if judgement == 'Disagree':
        if systemDeci == 'Toxic':
            return 'over-sensitive'
        else:
            return 'under-sensitive'
    else:
        return 'User Agrees with System'

def getAllEligiblePiecesOfEvidence(allUserReports, min_required_appearances=2, isResByTopic = True): 
    # Get all possible pieces of evidence
    allPossiblePiecesOfEvidence = []
    for r in allUserReports:
        currEvidenceList = r["evidence"]
        for e in currEvidenceList:
            allPossiblePiecesOfEvidence.append(e)
    
    # Go through the pieces of evidence to see which appear at least
    # minimum required appearances, which are set above
    res = {}
        # This structure of this work is:
        # item_id : evidenceObject
        # evidenceObject is structured as follows:
        # {
        #    num_appearances: _, 
        #    user_ids: [],
        #    verdicts: {user_id: verdict,...},
        #    topic: _, # Yes, this assumes that each piece of evidence can only be associated with one topic. This is a major ASSUMPTION.
        #    raw_evidence: {}
        # }
        # If we are going by resByTopic, we are going to have the following structure 
        # topic : {item_id : evidenceObject})
    
    for e in allPossiblePiecesOfEvidence:
        itemId = str(e['item_id'])
        userId = str(e['user_id'])
        topic = str(e['topic_']) #Yes, technically we should be using topic_id, but we don't really have a good mapper between topic_ and topic_id at this point.
        
        if topic in res:
            if itemId in res[topic]:
                currEvidenceObject = res[topic][itemId]
                # We need to update the currEvidenceObject
                # We assume that every user shares each piece of evidence once.
                currEvidenceObject['num_appearances'] = currEvidenceObject['num_appearances'] + 1
                currEvidenceObject['user_ids'].append(userId)
                currEvidenceObject['verdicts'][str(userId)] = getTranslatedVerdict(e['system_decision'], e['judgment'])
            else:
                #We need to create the currEvidenceObject from scratch.
                currEvidenceObject = {}
                currEvidenceObject['num_appearances'] = 1
                currEvidenceObject['user_ids'] = []
                currEvidenceObject['user_ids'].append(userId)
                currEvidenceObject['verdicts'] = {}
                currEvidenceObject['verdicts'][str(userId)] = getTranslatedVerdict(e['system_decision'], e['judgment'])
                currEvidenceObject['topic'] = topic
                currEvidenceObject['raw_evidence'] = e 
                res[topic][itemId] = currEvidenceObject #{num_appearances: 1, user_ids: [e['user_id']]}
        else:
            res[topic] = {}
    print ("All Evidence parsed ", res)
    
    # Now that we have figured out how often each piece of evidence has appeared, we will
    # filter out the pieces of evidence that don't fit the threshold
    itemIdsPastThreshold = set()
    contributorUserIds = set()
    for topic in res:
        for itemId in list(res[topic]):
            if res[topic][itemId]['num_appearances'] < min_required_appearances:
                print ("Removing item: ", itemId)
                res[topic].pop(itemId)
            else:
                itemIdsPastThreshold.add(itemId)
                for e in res[topic][itemId]['user_ids']:
                    contributorUserIds.add(e)
    print (itemIdsPastThreshold)
    print (contributorUserIds)
    print ("Results from parsing:")
    print (res)
    return (itemIdsPastThreshold, contributorUserIds, res)

def generateReport(allUserReports, itemIdsPastThreshold, contributorUserIds, parsedEvi):
    f = open(os.getcwd() + '/aggregated_user_reports.txt', 'w')
    consensusByTopic = {}
    for topic in parsedEvi:
        print("Summarize issue by example")
        consensusByTopic[topic] = summarizeIssuesByExample(f, parsedEvi[topic])
    # Write the executive summary
    writeExecutiveSummary(f, consensusByTopic, parsedEvi)
    # Write the elaborated areas
    f.write("\n-------------------------------------------------\n\n")
    for topic in consensusByTopic:
        currTopicConsensus = consensusByTopic[topic]
        if currTopicConsensus == 'over-sensitive' or currTopicConsensus == 'under-sensitive':
            f.write('\n[Consolidated Data] The system is ' + currTopicConsensus + ' on comments involving ' + topic)
        elif currTopicConsensus == 'No user consensus' or currTopicConsensus == 'Users Agree with System':
            f.write('\n[Consolidated Data] ' + currTopicConsensus + ' on comments involving ' + topic)
        writeIssuesByExampleRawDataSection(f, parsedEvi[topic])
    # Consolidate all user report summaries together
    # TODO: Group the user report summaries by similarity in text
    writeIndividualSummaries(f, allUserReports, contributorUserIds)

def writeIndividualSummaries(f, allUserReports, contributorUserIds):
	f.write("\n-------------------------------------------------\n\nConsolidated User Summaries:\n")
	for r in allUserReports:
		print (r)
		# Check if the report is from a user passed the contributing criteria
		currUserId = r['evidence'][0]['user_id']
		if currUserId in contributorUserIds and len(r['text_entry']) > 0:
			f.write("\n\nUser "+currUserId+ "'s Individual Report Summary:\n"+r['text_entry'])


def writeExecutiveSummary(f, consensusByTopic, parsedEvi):

    # Writing the header
    f.write("Executive Summary")
    f.write("\n\nExamined System: " + "Perspective API") #TODO: Make it variable
    #TODO: Include when the information was collected.
    f.write("\n\nFrom users' feedback to individual comments, we see the following issues:")

    for t in consensusByTopic:
        writeTopicExecutiveSummary(f, t, consensusByTopic, parsedEvi)

    f.write("\n\n")

def writeTopicExecutiveSummary(f, t, consensusByTopic, parsedEvi):
    # Write the summary line
    writeTopicExecutiveSummaryTopLine(f, t, consensusByTopic[t])
    # Give details, including: instances reported by end users & % of users aligned
    f.write("\n\t* "+ str(len(parsedEvi[t])-1)+ " instances were identified by end users")
    

def writeTopicExecutiveSummaryTopLine(f, t, currTopicConsensus):
    f.write("\n")
    if currTopicConsensus == 'over-sensitive' or currTopicConsensus == 'under-sensitive':
        f.write("The system is " + currTopicConsensus + " on comments involving the topic " + t)
    elif currTopicConsensus == 'no user consensus':
        outputStr = "Users disagree over whether the system is over-sensitive, under-sensitive, or correct on comments involving the topic "+t
        outputStr = outputStr + "This likely indicates more fundamental disagreement on what harm means."
        f.write(outputStr)
    else: # This is the case that users agree with the system
        f.write("Users agree with the system on comments involving the topic "+t)

def writeIssuesByExampleRawDataSection(f, topicSpecificEvi):        
    for eId in topicSpecificEvi:
        if eId == 'consensusDets':
            break
        currEvi = topicSpecificEvi[eId]
        print ('What is going on with currEvi?')
        print (currEvi)
        rawEvi = currEvi.get('raw_evidence')
        print(rawEvi)
        f.write('\n\n\tComment: \'' + rawEvi['comment_'] + '\'')
        f.write('\n\t\tSystem decision: ' + rawEvi['system_decision'])
        if topicSpecificEvi['consensusDets'][eId] == 'over-sensitive' or topicSpecificEvi['consensusDets'][eId] == 'under-sensitive':
            f.write('\n\t\tUser Consensus: The system is ' + topicSpecificEvi['consensusDets'][eId])
        else:
            f.write("\n\t\t" + topicSpecificEvi['consensusDets'][eId])
        f.write('\n\n\t\tRaw data:')
        f.write('\n\t\t\tUser\t\t | User Verdict')
        f.write('\n\t\t\t------------ | ------------------------')
        for userId in currEvi['verdicts']:
            f.write('\n\t\t\t' + userId + '\t\t\t | ' + currEvi['verdicts'][userId])

# The return value is the consensus around a topic. It can appear as:
#   'No user consensus'
#   'over-sensitive'
#   'under-sensitive'
#   'Users Agree with System'
def summarizeIssuesByExample(f, topicSpecificEvi):
    #print (topicSpecificEvi)
    #f.write(str(topicSpecificEvi))
    # Determine if  users believe the system are oversensitive or undersensitive
    #   This is defined as to whether all comments are considered oversensitive or undersensitive.
    #   A comment is considered oversensitive or undersensitive if >70% of user decisions align.
    evidenceSummary = {} 
    for eId in topicSpecificEvi:
        currEvi = topicSpecificEvi[eId]
        evidenceSummary[eId] = calcEviUserConsensus(currEvi)
    topicSpecificEvi['consensusDets'] = evidenceSummary
    currentConsensus = 'Placeholder'
    for eId in evidenceSummary:
        if currentConsensus == 'Placeholder':
            currentConsensus = evidenceSummary[eId]
        elif evidenceSummary[eId] != currentConsensus:
            currentConsensus = 'no user consensus'
            break
    return currentConsensus            
        

# This function can return 4 options the provided evidence:
#   1) over-sensitive - at least THRESHOLD percent of users agree that the system was oversensitive.
#   2) under-sensitive - at least THRESHOLD percent of users agree that the system was undersensitive. 
#   3) Correct - at least THRESHOLD percent of users agree with the system's determination.
#   4) Mixed - none of the categories could reach THRESHOLD percent of users.
# Threshold can be set when called but will default to 70%. 
def calcEviUserConsensus(currEvi, threshold=.7):
    # Calculate the number of users under each category
    numOver = 0
    numUnder = 0
    numCorrect = 0
    for v in currEvi['verdicts'].values():
        if v == 'over-sensitive':
            numOver = numOver + 1 
        elif v == 'under-sensitive':
            numUnder = numUnder + 1
        else:
            numCorrect = numCorrect + 1
    ttlUserReports = currEvi['num_appearances']
    print (str(numOver))
    print (str(numUnder))
    print (str(numCorrect))
    print ('Total:' + str(ttlUserReports))
    print (str(numOver/ttlUserReports))
    if numOver/ttlUserReports >= threshold:
        return 'over-sensitive'
    if numUnder/ttlUserReports >= threshold:
        return 'under-sensitive'
    if numCorrect/ttlUserReports >= threshold:
        return 'Users Agree with System'
    #return 'Fewer than ' + str(threshold * 100) + '% users agreed on a single category.'
    return 'no user consensus'

def generateObsoleteREport(allUserReports, itemIdsPastThreshold, contributorUserIds, allPossiblePiecesOfEvidence):
    # Now that we know which pieces of evidence have passed the threshold, let's gather the raw pieces of information
    aggregatedReportRawEvidence = {}
        # This will be in the format of:
            # { itemId: [the raw evidence dictionary] }
            # We need the raw evidence dictionaries for each user because the
            # end user model creates different predictions.
    listOfRelevantSummaries = []
        # This will be a list of the following object: {text_entry, user_id}
    for r in allUserReports:
        contributingReport = False
        for e in r["evidence"]:
            currItemId = str(e["item_id"])
            if currItemId in itemIdsPastThreshold:
                contributingReport = True
                print ("We have a contributing report!")
                if currItemId in aggregatedReportRawEvidence:
                    rawEvidenceList = aggregatedReportRawEvidence[currItemId]
                    rawEvidenceList.append(e)
                    aggregatedReportRawEvidence[currItemId] = rawEvidenceList
                else:
                    aggregatedReportRawEvidence[currItemId] = [e]
        if contributingReport:
           listOfRelevantSummaries.append({'text_entry': r['text_entry'],
                    'user_id': r["evidence"][0]["user_id"]})
    print ("Aggregated raw entries", aggregatedReportRawEvidence)
    print ("List of summaries", listOfRelevantSummaries)

    # Now that we know which summaries and aggregate raw entries need to be shown, let's aggregate them together!
    f = open(os.getcwd() + '/aggregated_user_reports.txt', 'w')
    f.write("This report aggregates user reports submitted by end users for the Perspective API.")
    f.write("\n\n\nAggregated End User Summaries:")
    for sum in listOfRelevantSummaries:
        f.write("\n\nUser " + sum["user_id"] + "\'s Report Summary/Suggestions:")
        f.write("\n\t" + sum["text_entry"])

    f.write("\n\n\nList of Evidence Listed from End Users:")
    iterator = 1
    for itemId in aggregatedReportRawEvidence:
        f.write("\n\nEvidence " + str(iterator) + ":")
        f.write("\n\tComment Text: \"" + aggregatedReportRawEvidence[itemId][0]["comment_"] + "\"")
        f.write("\n\titem_id: " + itemId)
        
        # Go over each user's reaction:
        for i in range(len(aggregatedReportRawEvidence[itemId])):
            currentUserEvidence = aggregatedReportRawEvidence[itemId][i]
            f.write("\n\t\tUser " + currentUserEvidence["user_id"] + "\'s Feedback:")
            agreeWithAPI = "True"
            if (currentUserEvidence["judgment"] != "Disagree"):
                agreeWithAPI = "False"
            f.write("\n\t\t\tUser Disagrees with System: " + agreeWithAPI)
            f.write("\n\t\tPerspective Score: ")
            f.write("\n\t\t\tGuide: This score has a 0 to 1 range, with 1 as the most toxic.")
            f.write("\n\t\t\tPerspective API's: " + str(currentUserEvidence["persp_score_avg"]))
            f.write("\tEnd User's Model: " + str(currentUserEvidence["persp_score_"]))
            f.write("\n")
        iterator = iterator + 1
    f.close()

    return itemIdsPastThreshold, contributorUserIds

if __name__ == "__main__":
    main()
