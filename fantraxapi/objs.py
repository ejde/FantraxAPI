from datetime import datetime, timedelta

from .exceptions import FantraxException


class DraftPick:
    """ Represents a single Draft Pick.

        Attributes:
            from_team (:class:`~Team`]): Team Traded From.
            to_team (:class:`~Team`]): Team Traded To.
            round (int): Draft Pick Round.
            year (int): Draft Pick Year.
            owner (:class:`~Team`]): Original Pick Owner.

    """
    def __init__(self, api, data):
        self._api = api
        self.from_team = self._api.team(data["from"]["teamId"])
        self.to_team = self._api.team(data["to"]["teamId"])
        self.round = data["draftPick"]["round"]
        self.year = data["draftPick"]["year"]
        self.owner = self._api.team(data["draftPick"]["origOwnerTeam"]["id"])

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"From: {self.from_team.name} To: {self.to_team.name} Pick: {self.year}, Round {self.round} ({self.owner.name})"


class Matchup:
    """ Represents a single Matchup.

        Attributes:
            matchup_key (int): Team ID.
            away (:class:`~Team`): Away Team.
            away_score (float): Away Team Score.
            home (:class:`~Team`): Home Team.
            home_score (float): Home Team Score.

    """
    def __init__(self, api, matchup_key, data):
        self._api = api
        self.matchup_key = matchup_key
        try:
            self.away = self._api.team(data[0]["teamId"])
        except FantraxException:
            self.away = data[0]["content"]
        self.away_score = float(str(data[1]["content"]).replace(',', ''))
        try:
            self.home = self._api.team(data[2]["teamId"])
        except FantraxException:
            self.home = data[2]["content"]
        self.home_score = float(str(data[3]["content"]).replace(',', ''))

    def winner(self):
        if self.away_score > self.home_score:
            return self.away, self.away_score, self.home, self.home_score
        elif self.away_score < self.home_score:
            return self.home, self.home_score, self.away, self.away_score
        else:
            return None, None, None, None

    def difference(self):
        if self.away_score > self.home_score:
            return self.away_score - self.home_score
        elif self.away_score < self.home_score:
            return self.home_score - self.away_score
        else:
            return 0

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.away} ({self.away_score}) vs {self.home} ({self.home_score})"


class Player:
    """ Represents a single Player.

        Attributes:
            id (str): Player ID.
            name (str): Player Name.
            short_name (str): Player Short Name.
            team_name (str): Team Name.
            team_short_name (str): Team Short Name.
            pos_short_name (str): Player Positions.
            positions (List[Position]): Player Positions.

    """
    def __init__(self, api, data, transaction_type=None):
        self._api = api
        self.type = transaction_type
        self.id = data["scorerId"]
        self.name = data["name"]
        self.short_name = data["shortName"]
        self.team_name = data["teamName"]
        self.team_short_name = data["teamShortName"] if "teamShortName" in data else self.team_name
        self.pos_short_name = data["posShortNames"]
        self.positions = [self._api.positions[d] for d in data["posIdsNoFlex"]]
        self.all_positions = [self._api.positions[d] for d in data["posIds"]]
        self.injured = False
        self.suspended = False
        if "icons" in data:
            for icon in data["icons"]:
                if icon["typeId"] in ["1", "2", "6"]: # DtD, Out, IR
                    self.injured = True
                elif icon["typeId"] == "6":
                    self.suspended = True


    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.type} {self.name}" if self.type else self.name


class Position:
    """ Represents a single Position.

        Attributes:
            id (str): Position ID.
            name (str): Position Name.
            short_name (str): Position Short Name.

    """
    def __init__(self, api, data):
        self._api = api
        self.id = data["id"]
        self.name = data["name"]
        self.short_name = data["shortName"]

    def __eq__(self, other):
        return (self.id, self.name, self.short_name) == (other.id, other.name, other.short_name)

class ScoringPeriod:
    """ Represents a single Scoring Period.

        Attributes:
            name (str): Name.
            week (int): Week Number.
            start (datetime): Start Date of the Period.
            end (datetime): End Date of the Period.
            next (datetime): Next Day after the Period.
            complete (bool): Is the Period Complete?
            current (bool): Is it the current Period?
            future (bool): Is the Period in the future?
            matchups (List[:class:`~Matchup`]): List of Matchups.

    """
    def __init__(self, api, data):
        self._api = api
        self.name = data["caption"]
        if self.name.startswith("Scoring Period "):
            self.week = int(self.name[15:])
        if self.name.startswith("Playoffs - Round "):
            self.week = int(self.name[17:])
        dates = data["subCaption"][1:-1].split(" - ")
        self.start = datetime.strptime(dates[0], "%a %b %d, %Y")
        self.end = datetime.strptime(dates[1], "%a %b %d, %Y")
        self.next = self.end + timedelta(days=1)
        self.days = (self.next - self.start).days
        now = datetime.now()
        self.complete = now > self.next
        self.current = self.start < now < self.next
        self.future = now < self.start

        self.matchups = []
        for i, matchup in enumerate(data["rows"], 1):
            self.matchups.append(Matchup(self._api, i, matchup["cells"]))

    def add_matchups(self, data):

        for i, matchup in enumerate(data["rows"], len(self.matchups) + 1):
            self.matchups.append(Matchup(self._api, i, matchup["cells"]))

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        output = f"{self.name}\n{self.days} Days ({self.start.strftime('%a %b %d, %Y')} - {self.end.strftime('%a %b %d, %Y')})"
        if self.complete:
            output += "\nComplete"
        elif self.current:
            output += "\nCurrent"
        else:
            output += "\nFuture"
        for matchup in self.matchups:
            output += f"\n{matchup}"
        return output


class Record:
    """ Represents a single Record of a :class:`~Standings`.

        Attributes:
            team (:class:`~Team`): Team.
            rank (int): Standings Rank.
            data (dict): key is header, value is the value for the team

    """
    def __init__(self, api, team_id, rank, data):
        self._api = api
        self.team = self._api.team(team_id)
        self.rank = int(rank)
        self.data = data

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        """
        Returns a human-readable string representation of the Record instance.
        
        Example:
            "Rank 1: Team Name
             Rotisserie Points: 32
             +/-: 1
             Waiver Wire Claim Order: 4
             ..."
        """
        # Start with the rank and team name
        record_str = f"Rank {self.rank}: {self.team.name}\n"

        # Iterate over the data dictionary and append each key-value pair
        for header, value in self.data.items():
            record_str += f"  {header}: {value}\n"
        
        return record_str.strip()

class StandingsCollection:
    """ Represents multiple Standings, e.g. for rotisserie-based leagues

        Attributes:
            week (int): Week Number.
            standings (List[:class:`~SingleStanding`]): List of Standing sections.

    """
    def __init__(self, api, data, week=None):
        self._api = api
        self.week = week
        self.standings = []
        
        for section in data:
            if section.get("tableType") != "SECTION_HEADING":
                self.standings.append({section.get("caption"): Standings(self._api, section)})

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        output = f"Standings"
        if self.week:
            output += f" Week {self.week}"
        for standing in self.standings:
            output += f"\n{standing}"
        return output


class Standings:
    """ Represents a single Standings table

        Attributes:
            table_type (str): Type of the table (e.g., "Rotisserie").
            caption (str): Caption of the standing.
            team_reacord (List[:class:`~Record`]): Team Ranks and their Records.
    """
    def __init__(self, api, section):
        self._api = api
        self.table_type = section.get("tableType")
        self.caption = section.get("caption")
        self.team_records = []

        header_names = [cell['name'] for cell in section['header']['cells']]

        for row in section['rows']:
            # Extract the 'cells' from the current row
            cells = row['cells']
            
            # Create a dictionary for the current row
            row_dict = {}
            
            # Zip header names with cell contents
            for header, cell in zip(header_names, cells):
                row_dict[header] = cell.get('content', None)  # Use .get to handle missing 'content'
            
            # Optionally, include fixedCells if needed
            fixed_cells = row.get('fixedCells', [])
            if len(fixed_cells) < 2:
                continue
            
            fixed_headers = row.get('fixedHeader', {}).get('cells', [])
            fixed_headers_names = [cell['name'] for cell in fixed_headers]
            for header, cell in zip(fixed_headers_names, fixed_cells):
                row_dict[header] = cell.get('content', None)
            
            team_id = fixed_cells[1].get("teamId")
            rank = fixed_cells[0].get("content")
            if team_id is not None and rank is not None:
                # Append the row dictionary to the result list
                self.team_records.append(Record(self._api, team_id, rank, row_dict))

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        output = f"Standing: {self.caption}"
        for record in self.team_records:
            output += f"\n{record}"
        return output


class Team:
    """ Represents a single Team.

        Attributes:
            team_id (str): Team ID.
            name (str): Team Name.
            short (str): Team Short Name.

    """
    def __init__(self, api, team_id, name, short, logo):
        self._api = api
        self.team_id = team_id
        self.name = name
        self.short = short
        self.logo = logo

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.name


class Trade:
    """ Represents a single Trade.

        Attributes:
            proposed_by (:class:`~Team`]): Team Trade Proposed By.
            proposed (str): Datetime Trade was Proposed.
            accepted (str): Datetime Trade was Accepted.
            executed (str): Datetime Trade will be Executed.
            moves (List[Union(:class:`~DraftPick`, :class:`~TradePlayer`)]): Team Short Name.

    """
    def __init__(self, api, data):
        self._api = api
        info = {i["name"]: i["value"] for i in data["usefulInfo"]}

        self.trade_id = data["txSetId"]
        self.proposed_by = self._api.team(data["creatorTeamId"])
        self.proposed = info["Proposed"]
        self.accepted = info["Accepted"]
        self.executed = info["To be executed"]
        self.moves = []
        for move in data["moves"]:
            self.moves.append(DraftPick(self._api, move) if "draftPick" in move else TradePlayer(self._api, move))

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "\n".join([str(m) for m in self.moves])


class TradeBlock:
    """ Represents a single Trade Block.

        Attributes:
            team (:class:`~Team`]): Team of the Trade Block.
            update_date (datetime): Last Updated Date.
            note (str): Trading Block Note.
            players_offered (Dict[str, List[Player]]): Players Offered.
            positions_wanted (Dict[str, List[Player]]): Players Wanted.
            positions_offered (List[Position]): Positions Offered.
            positions_wanted (List[Position]): Positions Wanted.
            stats_offered (List[str]): Stats Offered.
            stats_wanted (List[str]): Stats Wanted.

    """
    def __init__(self, api, data):
        self._api = api
        self.team = self._api.team(data["teamId"])
        self.update_date = datetime.fromtimestamp(data["lastUpdated"]["date"] / 1e3)
        self.note = data["comment"]["body"] if "comment" in data else ""
        self.players_offered = {self._api.positions[k].short_name: [Player(self._api, p) for p in players] for k, players in data["scorersOffered"]["scorers"].items()} if "scorersOffered" in data else {}
        self.players_wanted = {self._api.positions[k].short_name: [Player(self._api, p) for p in players] for k, players in data["scorersWanted"]["scorers"].items()} if "scorersWanted" in data else {}
        self.positions_offered = [self._api.positions[pos] for pos in data["positionsOffered"]["positions"]] if "positionsOffered" in data else []
        self.positions_wanted = [self._api.positions[pos] for pos in data["positionsWanted"]["positions"]] if "positionsWanted" in data else []
        self.stats_offered = [s["shortName"] for s in data["statsOffered"]["stats"]] if "statsOffered" in data else []
        self.stats_wanted = [s["shortName"] for s in data["statsWanted"]["stats"]] if "statsWanted" in data else []

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.note


class TradePlayer:
    """ Represents a single Draft Pick.

        Attributes:
            from_team (:class:`~Team`]): Team Traded From.
            to_team (:class:`~Team`]): Team Traded To.
            name (str): TradePlayer Name.
            short_name (str): TradePlayer Short Name.
            team_name (str): Team Name.
            team_short_name (str): Team Short Name.
            pos (str): TradePlayer Position.
            ppg (float): Fantasy Points Per Game.
            points (float): Total Fantasy Points.

    """
    def __init__(self, api, data):
        self._api = api
        self.from_team = self._api.team(data["from"]["teamId"])
        self.to_team = self._api.team(data["to"]["teamId"])
        self.name = data["scorer"]["name"]
        self.short_name = data["scorer"]["shortName"]
        self.team_name = data["scorer"]["teamName"]
        self.team_short_name = data["scorer"]["teamShortName"]
        self.pos = data["scorer"]["posShortNames"]
        self.ppg = data["scorePerGame"]
        self.points = data["score"]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"From: {self.from_team.name} To: {self.to_team.name} TradePlayer: {self.name} {self.pos} - {self.team_short_name} {self.ppg} {self.points}"


class Transaction:
    """ Represents a single Transaction.

        Attributes:
            id (str): Transaction ID.
            team (:class:`~Team`]): Team who made te Transaction.
            date (datetime): Transaction Date.
            count (str): Number of Players in the Transaction.
            players (List[Player]): Players in the Transaction.
            finalized (bool): this is true when all player have been added.

    """
    def __init__(self, api, data):
        self._api = api
        self.id = data["txSetId"]
        self.team = self._api.team(data["cells"][0]["teamId"])
        self.date = datetime.strptime(data["cells"][1]["content"], "%a %b %d, %Y, %I:%M%p")
        self.count = data["numInGroup"]
        self.players = [Player(self._api, data["scorer"], data["claimType"] if data["transactionCode"] == "CLAIM" else data["transactionCode"])]
        self.finalized = self.count == 1

    def update(self, data):
        if data["txSetId"] == self.id:
            self.players.append(Player(self._api, data["scorer"], data["claimType"] if data["transactionCode"] == "CLAIM" else data["transactionCode"]))
            self.finalized = True

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.players)


class Roster:
    def __init__(self, api, data, team_id):
        self._api = api
        self.team = self._api.team(team_id)
        self.active = data["miscData"]["statusTotals"][0]["total"]
        self.reserve = data["miscData"]["statusTotals"][1]["total"]
        self.max = data["miscData"]["statusTotals"][1]["max"]
        self.injured = data["miscData"]["statusTotals"][2]["total"]
        self.rows = []
        for group in data["tables"]:
            for row in group["rows"]:
                if "scorer" in row or row["statusId"] == "1":
                    self.rows.append(RosterRow(self._api, row))

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        rows = "\n".join([str(r) for r in self.rows])
        return f"{self.team} Roster\n{rows}"

class RosterRow:
    def __init__(self, api, data):
        self._api = api

        if data["statusId"] == "1":
            self.pos_id = data["posId"]
            self.pos = self._api.positions[self.pos_id]
        elif data["statusId"] == "3":
            self.pos_id = "-1"
            self.pos = Position(self._api, {"id": "-1", "name": "Injured", "shortName": "IR"})
        else:
            self.pos_id = "0"
            self.pos = Position(self._api, {"id": "0", "name": "Reserve", "shortName": "Res"})

        self.player = None
        self.fppg = None
        if "scorer" in data:
            self.player = Player(self._api, data["scorer"])
            self.fppg = float(data["cells"][3]["content"])

        content = data["cells"][1]["content"]
        self.opponent = None
        self.time = None
        if content and content.endswith(("AM", "PM")):
            self.opponent, time_str = content.split("\u003cbr/\u003e")
            self.time = datetime.strptime(time_str.split(" ")[1], "%I:%M%p")

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.player:
            return f"{self.pos.short_name}: {self.player}{f' vs {self.opponent}' if self.opponent else ''}"
        else:
            return f"{self.pos.short_name}: Empty"


