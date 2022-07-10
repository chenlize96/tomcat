import argparse
from datetime import datetime, timedelta
from enum import Enum
from glob import glob

from dateutil.parser import parse

from common import metadata_message_generator

TRIAL_TOPIC = "trial"
AGENT_DIALOG_TOPIC = "agent/dialog"
INTERVENTION_TOPIC = "agent/intervention/ASI_UAZ_TA1_ToMCAT/chat"


CHECK_UTTERANCE_TIME_WINDOW_SECONDS = 10


class Intervention:
    def __init__(self,
                 timestamp: datetime,
                 for_player: str) -> None:
        self.timestamp = timestamp
        self.for_player = for_player

    def __eq__(self, __o: object) -> bool:
        return self.timestamp == __o.timestamp and self.for_player == __o.for_player


class HelpRequestCritcalVictimIntervention(Intervention):
    def __init__(self, timestamp: datetime, for_player: str) -> None:
        super().__init__(timestamp, for_player)
        self.description = "help_request_for_critical_victim"
        self.expiration = timestamp + \
            timedelta(seconds=CHECK_UTTERANCE_TIME_WINDOW_SECONDS)
        self.compliance_criteria = ["CriticalVictim",
                                    "CriticalMarkerBlock",
                                    "critical"]


class HelpRequestRoomEscapeIntervention(Intervention):
    def __init__(self, timestamp: datetime, for_player: str) -> None:
        super().__init__(timestamp, for_player)
        self.description = "help_request_for_room_escape"
        self.expiration = timestamp + \
            timedelta(seconds=CHECK_UTTERANCE_TIME_WINDOW_SECONDS)
        self.compliance_criteria = ["Stuck",
                                    "HelpRequest",
                                    "NeedAction",
                                    "NeedItem",
                                    "NeedRole",
                                    "SOSMarker"]


class HelpRequestReplyIntervention(Intervention):
    def __init__(self, timestamp: datetime, for_player: str) -> None:
        super().__init__(timestamp, for_player)
        self.description = "help_request_reply"
        self.expiration = timestamp + \
            timedelta(seconds=CHECK_UTTERANCE_TIME_WINDOW_SECONDS)
        self.compliance_criteria = ["Stuck",
                                    "HelpRequest",
                                    "NeedAction",
                                    "NeedItem",
                                    "NeedRole",
                                    "SOSMarker"]


class MarkerBlockRegularVictimIntervention(Intervention):
    def __init__(self, timestamp: datetime, for_player: str) -> None:
        super().__init__(timestamp, for_player)
        self.description = "marker_block_regular_victim"
        self.expiration = timestamp + \
            timedelta(seconds=CHECK_UTTERANCE_TIME_WINDOW_SECONDS)
        self.compliance_criteria = ["RegularVictim",
                                    "RegularMarkerBlock",
                                    "regular"]


class MarkerBlockCriticalVictimIntervention(Intervention):
    def __init__(self, timestamp: datetime, for_player: str) -> None:
        super().__init__(timestamp, for_player)
        self.description = "marker_block_critical_victim"
        self.expiration = timestamp + \
            timedelta(seconds=CHECK_UTTERANCE_TIME_WINDOW_SECONDS)
        self.compliance_criteria = ["CriticalVictim",
                                    "CriticalMarkerBlock",
                                    "critical"]


class MarkerBlockVictimAIntervention(Intervention):
    def __init__(self, timestamp: datetime, for_player: str) -> None:
        super().__init__(timestamp, for_player)
        self.description = "marker_block_victim_a"
        self.expiration = timestamp + \
            timedelta(seconds=CHECK_UTTERANCE_TIME_WINDOW_SECONDS)
        self.compliance_criteria = ["VictimTypeA",
                                    "TypeAMarker"]


class MarkerBlockVictimBIntervention(Intervention):
    def __init__(self, timestamp: datetime, for_player: str) -> None:
        super().__init__(timestamp, for_player)
        self.description = "marker_block_victim_b"
        self.expiration = timestamp + \
            timedelta(seconds=CHECK_UTTERANCE_TIME_WINDOW_SECONDS)
        self.compliance_criteria = ["VictimTypeB",
                                    "TypeBMarker"]


def extract_player_information(message) -> dict[str, str]:
    player_information = {}
    for player_data in message["data"]["client_info"]:
        player_information[player_data["playername"]
                           ] = player_data["participant_id"]

    return player_information


def extract_intervention(message, timestamp: datetime) -> list[Intervention]:
    explanation = message["data"]["explanation"]["info"].replace(
        "This intervention was triggered ", "")
    content = message["data"]["content"]

    interventions = []

    if "to ensure" in explanation:
        return interventions
    elif "did not ask" in explanation:
        if "critical victim" in explanation:
            for receiver in message["data"]["receivers"]:
                intervention = HelpRequestCritcalVictimIntervention(
                    timestamp, receiver)
                interventions.append(intervention)
        if "threat room" in explanation:
            for receiver in message["data"]["receivers"]:
                intervention = HelpRequestRoomEscapeIntervention(
                    timestamp, receiver)
                interventions.append(intervention)
    elif "did not get an answer" in explanation:
        for receiver in message["data"]["receivers"]:
            intervention = HelpRequestReplyIntervention(timestamp, receiver)
            interventions.append(intervention)
    elif "placed a marker" in explanation and "regular victim marker" in content:
        for receiver in message["data"]["receivers"]:
            intervention = MarkerBlockRegularVictimIntervention(
                timestamp, receiver)
            interventions.append(intervention)
    elif "placed a marker" in explanation and "critical victim marker" in content:
        for receiver in message["data"]["receivers"]:
            intervention = MarkerBlockCriticalVictimIntervention(
                timestamp, receiver)
            interventions.append(intervention)
    else:
        print("[INFO] Event is ignored: " +
              message["data"]["explanation"]["info"])

    return interventions


def log_report(output_dir: str, report: dict[str, any]) -> None:
    with open(output_dir + "/compliance_instances_report.txt", 'w') as file:
        for key, value in report.items():
            file.write(f"{key}: {value}\n")


if __name__ == "__main__":
    # parsing program arguments
    parser = argparse.ArgumentParser(
        description="Evaluate compliance in trials")
    parser.add_argument(
        "--data_dir",
        help="Directory containing .metadata files",
        default="/media/mule/projects/tomcat/protected/study-3_2022",
    )
    parser.add_argument(
        "--output_dir",
        help="Output directory",
        default=".",
    )
    args = parser.parse_args()

    report = {
        "num_interventions": 0,
        "num_compiled_interventions": 0,
        "num_intervention_help_request_for_critical_victim": 0,
        "num_complied_intervention_help_request_for_critical_victim": 0,
        "num_intervention_help_request_for_room_escape": 0,
        "num_complied_intervention_help_request_for_room_escape": 0,
        "num_intervention_help_request_reply": 0,
        "num_complied_intervention_help_request_reply": 0,
        "num_intervention_marker_block_regular_victim": 0,
        "num_complied_intervention_marker_block_regular_victim": 0,
        "num_intervention_marker_block_critical_victim": 0,
        "num_complied_intervention_marker_block_critical_victim": 0,
        "num_intervention_marker_block_victim_a": 0,
        "num_compiled_intervention_marker_block_victim_a": 0,
        "num_intervention_marker_block_victim_b": 0,
        "num_compiled_intervention_marker_block_victim_b": 0
    }

    for filepath in glob(args.data_dir + "/*T00*UAZ*.metadata"):
        player_information: dict[str, str] = {}
        watch_interventions: list[Intervention] = []

        trial_started = False

        for message in metadata_message_generator(filepath):
            timestamp = parse(message["msg"]["timestamp"])

            # resolve expired interventions
            watch_interventions = list(filter(
                lambda intervention: intervention.expiration >= timestamp,
                watch_interventions
            ))

            # parse trial message
            if "topic" in message and message["topic"] == TRIAL_TOPIC:
                # extract player information
                if message["msg"]["sub_type"] == "start":
                    player_information = extract_player_information(message)
                    trial_started = True
                    continue
                # end parsing after the trial has ended
                else:
                    break
            # only start monitoring after trial has started
            elif not trial_started:
                continue

            # parse ToMCAT intervention message
            if "topic" in message and message["topic"] == INTERVENTION_TOPIC:
                # ensure player identification consistency
                assert set(message["data"]["receivers"]).issubset(
                    player_information.values())

                interventions = extract_intervention(message, timestamp)
                watch_interventions += interventions

                for intervention in interventions:
                    if isinstance(intervention, HelpRequestCritcalVictimIntervention):
                        report["num_intervention_help_request_for_critical_victim"] += 1
                    elif isinstance(intervention, HelpRequestRoomEscapeIntervention):
                        report["num_intervention_help_request_for_room_escape"] += 1
                    elif isinstance(intervention, HelpRequestReplyIntervention):
                        report["num_intervention_help_request_reply"] += 1
                    elif isinstance(intervention, MarkerBlockRegularVictimIntervention):
                        report["num_intervention_marker_block_regular_victim"] += 1
                    elif isinstance(intervention, MarkerBlockCriticalVictimIntervention):
                        report["num_intervention_marker_block_critical_victim"] += 1
                    elif isinstance(intervention, MarkerBlockVictimAIntervention):
                        report["num_intervention_marker_block_victim_a"] += 1
                    elif isinstance(intervention, MarkerBlockVictimBIntervention):
                        report["num_intervention_marker_block_victim_b"] += 1
                    else:
                        raise RuntimeError(
                            "Failed to determine intervention type")

                report["num_interventions"] += len(interventions)

            # parse dialog agent message to check for compliance
            if "topic" in message and message["topic"] == AGENT_DIALOG_TOPIC:
                if message["data"]["participant_id"] == "Server":
                    continue

                # ensure player identification consistency
                assert message["data"]["participant_id"] in player_information.keys()

                # check for any intervention that has been complied by the subject
                complied_interventions = []
                for intervention in watch_interventions:
                    if player_information[message["data"]["participant_id"]] == intervention.for_player:
                        # check if the utterance label matches the compliance criteria
                        intervention_found = False
                        for compliance_tag in intervention.compliance_criteria:
                            for labels in message["data"]["extractions"]:
                                if compliance_tag in labels:
                                    complied_interventions.append(intervention)
                                    intervention_found = True
                                    break
                            if intervention_found:
                                break
                        # check if the utterance text contains any word that matches the compliance criteria
                        else:
                            if compliance_tag in message["data"]["text"]:
                                complied_interventions.append(intervention)

                for intervention in complied_interventions:
                    watch_interventions.remove(intervention)

                    if isinstance(intervention, HelpRequestCritcalVictimIntervention):
                        report["num_complied_intervention_help_request_for_critical_victim"] += 1
                    elif isinstance(intervention, HelpRequestRoomEscapeIntervention):
                        report["num_complied_intervention_help_request_for_room_escape"] += 1
                    elif isinstance(intervention, HelpRequestReplyIntervention):
                        report["num_complied_intervention_help_request_reply"] += 1
                    elif isinstance(intervention, MarkerBlockRegularVictimIntervention):
                        report["num_complied_intervention_marker_block_regular_victim"] += 1
                    elif isinstance(intervention, MarkerBlockCriticalVictimIntervention):
                        report["num_complied_intervention_marker_block_critical_victim"] += 1
                    elif isinstance(intervention, MarkerBlockVictimAIntervention):
                        report["num_complied_intervention_marker_block_victim_a"] += 1
                    elif isinstance(intervention, MarkerBlockVictimBIntervention):
                        report["num_complied_intervention_marker_block_victim_b"] += 1
                    else:
                        raise RuntimeError(
                            "Failed to determine intervention type")

                    report["num_compiled_interventions"] += 1

    log_report(args.output_dir, report)
