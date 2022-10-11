import os
import pickle
import pandas as pd

def main():
    allUserReports = getAllUserReports()
    allUserReports = removeAllIncompleteUserReports(allUserReports)
    getAllEligiblePiecesOfEvidence(allUserReports)

# TODO: Do a much more efficient implementation (This would require changing the format of the user reports.)

# This function retrieves all of the user reports collected from end users.
# Here, I'm assuming that all user reports are in the ./data/user_reports directory
def getAllUserReports():
    allUserReports = []
    userReportsDirectory = os.getcwd() + "/data/user_reports/"
    print ("Getting all user reports saved in ", userReportsDirectory)
    for filename in os.listdir(userReportsDirectory):
        if not filename.startswith('.'):
            f = pd.read_pickle(os.path.join(userReportsDirectory, filename))
            allUserReports.append(f)
    #print(allUserReports)
    return allUserReports


# Remove all incomplete end user reports and do some clean up (like removing the array).
def removeAllIncompleteUserReports(allUserReports):
    allCompleteUserReports = []
    for f in allUserReports:
        currReport = f[0] # We need to get to the JSON file without df
        if currReport['complete_status'] != True:
            print("Skipping an incomplete report")
        else:
            print("Going to do something with this report")
            allCompleteUserReports.append(currReport)
    return allCompleteUserReports

def getAllEligiblePiecesOfEvidence(allUserReports, min_required_appearances=2): 
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
        #   {num_appearances: _, 
        #    user_ids: []}
    for e in allPossiblePiecesOfEvidence:
        itemId = str(e['item_id'])
        userId = str(e['user_id'])
        if itemId in res:
            currEvidenceObject = res[itemId]
            # We need to update the currEvidenceObject
            # We assume that every user shares each piece of evidence once.
            currEvidenceObject['num_appearances'] = currEvidenceObject['num_appearances'] + 1
            currEvidenceObject['user_ids'].append(userId)
        else:
            #We need to create the currEvidenceObject from scratch.
            currEvidenceObject = {}
            currEvidenceObject['num_appearances'] = 1
            currEvidenceObject['user_ids'] = []
            currEvidenceObject['user_ids'].append(userId)
            res[itemId] = currEvidenceObject #{num_appearances: 1, user_ids: [e['user_id']]} 
    print ("All Evidence parsed ", res)
    
    # Now that we have figured out how often each piece of evidence has appeared, we will
    # filter out the pieces of evidence that don't fit the threshold
    itemIdsPastThreshold = set()
    contributorUserIds = set() 
    for itemId in res:
        if res[itemId]['num_appearances'] < min_required_appearances:
            print ("Removing item: ", itemId)
        else:
            itemIdsPastThreshold.add(itemId)
            for e in res[itemId]['user_ids']:
                contributorUserIds.add(e)
    print (itemIdsPastThreshold)
    print (contributorUserIds)

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
