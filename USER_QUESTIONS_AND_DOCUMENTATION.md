# Sejmofil Neo4j Database - User Questions and Documentation

## Database Overview

The Sejmofil database contains comprehensive Polish parliamentary data with 79,044 nodes and 191,720 relationships. It covers legislative processes, political activity, speeches, and voting records from the Polish parliament (Sejm).

### Key Statistics
- **Total Nodes**: 79,044
- **Total Relationships**: 191,720
- **MPs (Person nodes)**: 1,442
- **Political Parties (Club nodes)**: 9 active parties
- **Speeches (SAID relationships)**: 56,730
- **Legislative Documents (Print nodes)**: 2,022

## User Question Categories

### 1. Basic Information Questions

**Who is [MP Name]?**
- "Tell me about Krzysztof Bosak"
- "Who is the MP from Warsaw?"
- "What party does Andrzej Grzyb belong to?"

**What is [Political Party/Club]?**
- "What is PiS?"
- "How many members does KO have?"
- "Which party has the most MPs?"

**What are the current legislative activities?**
- "What bills are being discussed right now?"
- "Show me recent parliamentary activity"
- "What legislation passed recently?"

### 2. MP-Specific Questions

**Activity and Contributions**
- "What bills has [MP] authored?"
- "How many speeches has [MP] given?"
- "What committees is [MP] on?"
- "What topics does [MP] focus on?"

**Personal Information**
- "Where is [MP] from?"
- "What is [MP]'s profession?"
- "How long has [MP] been in parliament?"

**Voting and Positions**
- "How did [MP] vote on [topic/bill]?"
- "What is [MP]'s stance on [issue]?"

### 3. Party/Club Questions

**Composition and Leadership**
- "Who leads [party]?"
- "How many active members does [party] have?"
- "Who are the MPs from [party]?"

**Activity and Focus**
- "What legislation has [party] proposed?"
- "What topics does [party] focus on?"
- "How active is [party] in parliament?"

### 4. Legislative Process Questions

**Bill Tracking**
- "What is the status of bill [number]?"
- "Who authored bill [number]?"
- "What stage is [bill] at?"

**Topic-Based Questions**
- "What bills are about [topic]?"
- "Who are the experts on [topic]?"
- "What legislation affects [topic]?"

### 5. Committee and Organizational Questions

**Committee Information**
- "What does [committee] do?"
- "Who is on [committee]?"
- "What bills has [committee] reviewed?"

**Government Structure**
- "What ministries are there?"
- "Who heads [ministry]?"
- "What organizations are involved in [topic]?"

### 6. Speech and Discussion Questions

**Parliamentary Debates**
- "What did [MP] say about [topic]?"
- "When did [MP] speak last?"
- "What are recent speeches about [topic]?"

**Sentiment and Opinions**
- "What is the sentiment about [bill/topic]?"
- "Who supports/opposes [bill]?"
- "What are the main arguments for/against [bill]?"

### 7. Voting and Decision Questions

**Voting Records**
- "How did parliament vote on [bill]?"
- "What was the result of voting [number]?"
- "Who voted yes/no on [issue]?"

**Party Voting Patterns**
- "How did [party] vote on [bill]?"
- "What is [party]'s position on [topic]?"
- "Are parties united on [issue]?"

### 8. Temporal Questions

**Recent Activity**
- "What happened in parliament today/last week?"
- "What new bills were introduced recently?"
- "What legislation passed recently?"

**Historical Questions**
- "What legislation was passed in [year/month]?"
- "How has [topic] evolved over time?"
- "What was [MP]'s activity like in previous terms?"

### 9. Comparative Questions

**MP Comparisons**
- "Who is the most active MP?"
- "Compare [MP1] and [MP2]'s activity"
- "Who speaks most about [topic]?"

**Party Comparisons**
- "Which party proposes the most legislation?"
- "Compare voting patterns of [party1] and [party2]"
- "Which party has the most committee members?"

### 10. Analytical Questions

**Trends and Patterns**
- "What are the most discussed topics?"
- "Which committees are most active?"
- "What legislation gets the most attention?"

**Impact and Effectiveness**
- "How successful is [party/MP] at passing legislation?"
- "What bills from [party] became law?"
- "Which topics have the most legislation?"

## Data Schema Details

### Node Properties

**Person**
- id: Unique identifier
- firstLastName: Full name (First Last)
- firstName, lastName: Name components
- club: Political party
- role: Parliamentary role (Poseł, Senator, etc.)
- active: Whether currently active
- districtName, districtNum: Constituency
- voivodeship: Province
- profession: Occupation
- educationLevel: Education level
- birthDate, birthLocation: Biographical info
- biography, biographyUrl: Extended information
- email: Contact information
- numberOfVotes: Votes received in election
- absents: Number of absences

**Club (Political Party)**
- id: Unique identifier
- name: Party name
- membersCount: Total members
- phone, fax, email: Contact information

**Print (Legislative Document)**
- number: Print number (e.g., "932")
- title: Document title
- summary: Document summary
- documentDate: Creation date
- changeDate: Last modification
- term: Parliamentary term
- processPrint: Related print numbers
- attachments: File attachments
- embedding: Vector embedding for semantic search

**Process (Legislative Process)**
- number: Process number
- title: Process title
- documentDate: Start date
- term: Parliamentary term
- description: Process description
- legislativeCommittee: Responsible committee
- urgencyStatus: Urgency level
- UE: EU-related flag

**Stage (Process Stage)**
- stageName: Stage name (e.g., "Pierwsze czytanie")
- date: Stage date
- number: Stage number
- type: Stage type
- decision: Decision made
- comment: Additional comments
- committeeCode: Committee involved
- rapporteurName, rapporteurID: Rapporteur information

**Statement (Speech/Statement)**
- statement_speaker: Speaker name
- statement_speaker_function: Speaker role
- statement_official_topic: Topic discussed
- statement_official_point: Agenda point
- proceeding_number, proceeding_date: Session info
- statement_source: Source URL
- order: Speech order

**Topic**
- name: Topic name
- description: Topic description
- embedding: Vector embedding

**Committee**
- code: Committee code
- name: Committee name
- nameGenitive: Committee name in genitive
- scope: Committee responsibilities
- type: Committee type (STANDING, etc.)
- phone: Contact information
- appointmentDate, compositionDate: Formation dates

**Organization**
- name: Organization name
- description: Organization description
- embedding: Vector embedding

**Voting**
- votingNumber: Voting number
- title: Voting title
- description: Voting description
- date: Voting date
- yes, no, abstain, notParticipating: Vote counts
- totalVoted: Total votes cast
- term: Parliamentary term
- topic: Related topic

**Act (Published Law)**
- ELI: European Legislation Identifier
- title: Law title
- status: Law status
- inForce: Whether in force
- entryIntoForce: Effective date
- publisher: Publishing body
- year: Publication year

### Relationship Properties

**SAID** (Person said Statement)
- date: Speech date

**COMMENTS** (Person comments on Print)
- summary: Comment summary
- sentiment: Sentiment analysis

**VOTED** (Person voted in Voting)
- Vote value (yes/no/abstain)

**HAS** (Various containment relationships)
- Properties vary by context

## Usage Examples for MCP Agent

### Simple Queries
1. "Who is the MP with the most speeches?"
2. "What are the top 5 most active committees?"
3. "Show me recent legislation about education"

### Complex Queries
1. "Find all MPs from Warsaw who are on the education committee"
2. "What legislation has PiS proposed about healthcare?"
3. "Compare the voting patterns of KO and PiS on economic issues"

### Analytical Queries
1. "Which party has the highest legislative success rate?"
2. "What topics are most frequently discussed in parliament?"
3. "How has the number of speeches changed over time?"

This database provides rich information about Polish parliamentary democracy, enabling detailed analysis of legislative processes, political activity, and democratic participation.