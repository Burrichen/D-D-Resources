---
_source: obsidian-dnd-v2
_source_path: Wiki/Characters/Character Database.md
_title: Character Database
_licence: own-work
_fetched: '2026-11-04T10:54:34+00:00'
_content_hash: sha256:5fff28fe2c9f179604a5e85e544eca4a59beeb23879a60fd561dfdd0ce00e042
database-plugin: basic
---

```yaml:dbfolder
name: new database
description: new description
columns:
  __file__:
    key: __file__
    id: __file__
    input: markdown
    label: File
    accessorKey: __file__
    isMetadata: true
    skipPersist: false
    isDragDisabled: false
    csvCandidate: true
    accessor: __file__
    position: 1
    isSorted: true
    isSortedDesc: false
    width: 201
    isHidden: false
    sortIndex: 1
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: true
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
  __created__:
    key: __created__
    id: __created__
    input: calendar_time
    label: Created
    accessorKey: __created__
    isMetadata: true
    isDragDisabled: false
    skipPersist: false
    csvCandidate: true
    accessor: __created__
    position: 25
    width: 150
    isHidden: false
    sortIndex: -1
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
  __modified__:
    key: __modified__
    id: __modified__
    input: calendar_time
    label: Modified
    accessorKey: __modified__
    isMetadata: true
    isDragDisabled: false
    skipPersist: false
    csvCandidate: true
    accessor: __modified__
    position: 26
    width: 150
    isHidden: false
    sortIndex: -1
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
  Alignment:
    input: select
    accessor: Alignment
    key: Alignment
    label: Alignment
    position: 4
    skipPersist: false
    accessorKey: Alignment
    width: -53
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Neutral", value: "Neutral", color: "hsl(99, 95%, 90%)"}
      - { label: "TN", value: "TN", color: "hsl(240, 95%, 90%)"}
      - { label: "CN", value: "CN", color: "hsl(177, 95%, 90%)"}
      - { label: "NG", value: "NG", color: "hsl(152, 95%, 90%)"}
      - { label: "LG", value: "LG", color: "hsl(287, 95%, 90%)"}
      - { label: "CG", value: "CG", color: "hsl(174, 95%, 90%)"}
      - { label: "CE", value: "CE", color: "hsl(131, 95%, 90%)"}
      - { label: "LE", value: "LE", color: "hsl(37, 95%, 90%)"}
      - { label: "NE", value: "NE", color: "hsl(172, 95%, 90%)"}
      - { label: "LN", value: "LN", color: "hsl(110, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
  Race:
    input: select
    accessor: Race
    key: Race
    label: Race
    position: 3
    skipPersist: false
    accessorKey: Race
    width: 221
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Aasimar", value: "Aasimar", color: "hsl(58, 63%, 58%)"}
      - { label: "Bugbear", value: "Bugbear", color: "hsl(29, 29%, 58%)"}
      - { label: "Dhampir", value: "Dhampir", color: "hsl(11, 81%, 28%)"}
      - { label: "Dragonborn", value: "Dragonborn", color: "hsl(6, 80%, 44%)"}
      - { label: "Drow", value: "Drow", color: "hsl(85, 9%, 32%)"}
      - { label: "Dwarf", value: "Dwarf", color: "hsl(183, 95%, 90%)"}
      - { label: "Eladrin", value: "Eladrin", color: "hsl(163, 63%, 28%)"}
      - { label: "Firbolg", value: "Firbolg", color: "hsl(39, 11%, 37%)"}
      - { label: "Genasi", value: "Genasi", color: "hsl(200, 30%, 37%)"}
      - { label: "Goliath", value: "Goliath", color: "hsl(200, 1%, 37%)"}
      - { label: "Half-Elf", value: "Half-Elf", color: "hsl(67, 26%, 83%)"}
      - { label: "High Elf", value: "High Elf", color: "hsl(163, 83%, 57%)"}
      - { label: "Human", value: "Human", color: "hsl(13, 95%, 90%)"}
      - { label: "Orc", value: "Orc", color: "hsl(117, 29%, 35%)"}
      - { label: "Shader-Kai", value: "Shader-Kai", color: "hsl(63, 14%, 18%)"}
      - { label: "Tiefling", value: "Tiefling", color: "hsl(29, 95%, 90%)"}
      - { label: "Vampire", value: "Vampire", color: "hsl(11, 81%, 28%)"}
      - { label: "Wood Elf", value: "Wood Elf", color: "hsl(42, 50%, 36%)"}
      - { label: "Yuan-Ti", value: "Yuan-Ti", color: "hsl(125, 89%, 14%)"}
      - { label: "Mind-Flayer", value: "Mind-Flayer", color: "hsl(82, 95%, 90%)"}
      - { label: "Other", value: "Other", color: "hsl(355, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
  Gender:
    input: select
    accessor: Gender
    key: Gender
    label: Gender
    position: 5
    skipPersist: false
    accessorKey: Gender
    width: 101
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Female", value: "Female", color: "hsl(111, 95%, 90%)"}
      - { label: "Male", value: "Male", color: "hsl(74, 95%, 90%)"}
      - { label: "N/A", value: "N/A", color: "hsl(296, 95%, 90%)"}
      - { label: "Other", value: "Other", color: "hsl(345, 95%, 90%)"}
      - { label: "Non-Binary", value: "Non-Binary", color: "hsl(93, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
      option_source: manual
  Age:
    input: select
    accessor: Age
    key: Age
    label: Age
    position: 13
    skipPersist: false
    accessorKey: Age
    width: 150
    isHidden: false
    sortIndex: -1
    isSorted: false
    isSortedDesc: false
    options:
      - { label: "Adult", value: "Adult", color: "hsl(4, 95%, 90%)"}
      - { label: "Ancient", value: "Ancient", color: "hsl(270, 95%, 90%)"}
      - { label: "Child", value: "Child", color: "hsl(271, 95%, 90%)"}
      - { label: "Elderly", value: "Elderly", color: "hsl(231, 95%, 90%)"}
      - { label: "Infant", value: "Infant", color: "hsl(94, 95%, 90%)"}
      - { label: "Teen", value: "Teen", color: "hsl(328, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
  NoteIcon:
    input: select
    accessor: NoteIcon
    key: NoteIcon
    label: NoteIcon
    position: 8
    skipPersist: false
    accessorKey: NoteIcon
    width: 150
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Character", value: "Character", color: "hsl(221, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
  Condition:
    input: tags
    accessor: Condition
    key: Condition
    label: Condition
    position: 14
    skipPersist: false
    accessorKey: Condition
    width: 150
    isHidden: false
    sortIndex: -1
    isSorted: false
    isSortedDesc: true
    options:
      - { label: "Dead", value: "Dead", color: "hsl(280, 95%, 90%)"}
      - { label: "Undead", value: "Undead", color: "hsl(323, 95%, 90%)"}
      - { label: "Dying", value: "Dying", color: "hsl(323, 95%, 90%)"}
      - { label: "Healthy", value: "Healthy", color: "hsl(342, 95%, 90%)"}
      - { label: "Hurt", value: "Hurt", color: "hsl(10, 95%, 90%)"}
      - { label: "Sick", value: "Sick", color: "hsl(80, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
  Location:
    input: select
    accessor: Location
    key: Location
    label: Location
    position: 15
    skipPersist: false
    accessorKey: Location
    width: 150
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Oxwick", value: "Oxwick", color: "hsl(26, 95%, 90%)"}
      - { label: "Midmore", value: "Midmore", color: "hsl(282, 95%, 90%)"}
      - { label: "The Keep", value: "The Keep", color: "hsl(119, 95%, 90%)"}
      - { label: "Orlane", value: "Orlane", color: "hsl(10, 95%, 90%)"}
      - { label: "Khundhur", value: "Khundhur", color: "hsl(137, 95%, 90%)"}
      - { label: "Clithe", value: "Clithe", color: "hsl(316, 95%, 90%)"}
      - { label: "Prydewick", value: "Prydewick", color: "hsl(64, 95%, 90%)"}
      - { label: "Or'thumph", value: "Or'thumph", color: "hsl(325, 95%, 90%)"}
      - { label: "Lapsarian Federation", value: "Lapsarian Federation", color: "hsl(60, 95%, 90%)"}
      - { label: "Nuria Natal", value: "Nuria Natal", color: "hsl(320, 95%, 90%)"}
      - { label: "Heresy", value: "Heresy", color: "hsl(70, 95%, 90%)"}
      - { label: "Ozara Desert", value: "Ozara Desert", color: "hsl(226, 95%, 90%)"}
      - { label: "Khensun Tower", value: "Khensun Tower", color: "hsl(155, 95%, 90%)"}
      - { label: "Pidewick", value: "Pidewick", color: "hsl(78, 95%, 90%)"}
      - { label: "Cirque Du Freak", value: "Cirque Du Freak", color: "hsl(138, 95%, 90%)"}
      - { label: "Valera", value: "Valera", color: "hsl(249, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
      option_source: manual
  Alias:
    input: text
    accessor: Alias
    key: Alias
    label: Alias
    position: 2
    skipPersist: false
    accessorKey: Alias
    width: 176
    isHidden: false
    sortIndex: -1
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
  Occupation:
    input: tags
    accessor: Occupation
    key: Occupation
    label: Occupation
    position: 17
    skipPersist: false
    accessorKey: Occupation
    width: 132
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Adventurer", value: "Adventurer", color: "hsl(232, 95%, 90%)"}
      - { label: "Alchemist", value: "Alchemist", color: "hsl(204, 95%, 90%)"}
      - { label: "Archeologist", value: "Archeologist", color: "hsl(66, 95%, 90%)"}
      - { label: "Barkeeper", value: "Barkeeper", color: "hsl(68, 95%, 90%)"}
      - { label: "Blacksmith", value: "Blacksmith", color: "hsl(66, 95%, 90%)"}
      - { label: "Courier", value: "Courier", color: "hsl(164, 95%, 90%)"}
      - { label: "Druid", value: "Druid", color: "hsl(164, 95%, 90%)"}
      - { label: "Enchanter", value: "Enchanter", color: "hsl(178, 95%, 90%)"}
      - { label: "Farmer", value: "Farmer", color: "hsl(70, 95%, 90%)"}
      - { label: "Guard", value: "Guard", color: "hsl(320, 95%, 90%)"}
      - { label: "Historian", value: "Historian", color: "hsl(24, 95%, 90%)"}
      - { label: "Libarian", value: "Libarian", color: "hsl(7, 95%, 90%)"}
      - { label: "Mage", value: "Mage", color: "hsl(194, 95%, 90%)"}
      - { label: "Merchant", value: "Merchant", color: "hsl(140, 95%, 90%)"}
      - { label: "Noble", value: "Noble", color: "hsl(28, 95%, 90%)"}
      - { label: "Priest", value: "Priest", color: "hsl(322, 95%, 90%)"}
      - { label: "Royal", value: "Royal", color: "hsl(126, 95%, 90%)"}
      - { label: "Ruler", value: "Ruler", color: "hsl(324, 95%, 90%)"}
      - { label: "Servant", value: "Servant", color: "hsl(249, 95%, 90%)"}
      - { label: "Stablehand", value: "Stablehand", color: "hsl(25, 95%, 90%)"}
      - { label: "Steward", value: "Steward", color: "hsl(339, 95%, 90%)"}
      - { label: "Teacher", value: "Teacher", color: "hsl(36, 95%, 90%)"}
      - { label: "Hunter", value: "Hunter", color: "hsl(308, 95%, 90%)"}
      - { label: "Warrior", value: "Warrior", color: "hsl(295, 95%, 90%)"}
      - { label: "Beggar", value: "Beggar", color: "hsl(313, 95%, 90%)"}
      - { label: "Leader", value: "Leader", color: "hsl(352, 95%, 90%)"}
      - { label: "Artificer", value: "Artificer", color: "hsl(8, 95%, 90%)"}
      - { label: "Researcher", value: "Researcher", color: "hsl(348, 95%, 90%)"}
      - { label: "Pirate", value: "Pirate", color: "hsl(206, 95%, 90%)"}
      - { label: "Cultist", value: "Cultist", color: "hsl(240, 95%, 90%)"}
      - { label: "Goddess", value: "Goddess", color: "hsl(152, 95%, 90%)"}
      - { label: "Sheriff", value: "Sheriff", color: "hsl(151, 95%, 90%)"}
      - { label: "Bounty Hunter", value: "Bounty Hunter", color: "hsl(324, 95%, 90%)"}
      - { label: "Rogue", value: "Rogue", color: "hsl(269, 95%, 90%)"}
      - { label: "Monk", value: "Monk", color: "hsl(41, 95%, 90%)"}
      - { label: "Performer", value: "Performer", color: "hsl(105, 95%, 90%)"}
      - { label: "Architecht", value: "Architecht", color: "hsl(181, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
  AssociatedGroup:
    input: tags
    accessor: AssociatedGroup
    key: AssociatedGroup
    label: AssociatedGroup
    position: 18
    skipPersist: false
    accessorKey: AssociatedGroup
    width: 150
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Bilgerats", value: "Bilgerats", color: "hsl(275, 95%, 90%)"}
      - { label: "The Five Nobels", value: "The Five Nobels", color: "hsl(10, 95%, 90%)"}
      - { label: "The Ambit", value: "The Ambit", color: "hsl(213, 95%, 90%)"}
      - { label: "The Burning Rune", value: "The Burning Rune", color: "hsl(101, 95%, 90%)"}
      - { label: "The Golden God's Champions", value: "The Golden God's Champions", color: "hsl(75, 95%, 90%)"}
      - { label: "Cirque Du Freak", value: "Cirque Du Freak", color: "hsl(210, 95%, 90%)"}
      - { label: "Valorium Order", value: "Valorium Order", color: "hsl(260, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
  AssociatedReligion:
    input: tags
    accessor: AssociatedReligion
    key: AssociatedReligion
    label: AssociatedReligion
    position: 19
    skipPersist: false
    accessorKey: AssociatedReligion
    width: 78
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Gond", value: "Gond", color: "hsl(313, 95%, 90%)"}
      - { label: "Sune", value: "Sune", color: "hsl(246, 95%, 90%)"}
      - { label: "Golden God", value: "Golden God", color: "hsl(132, 95%, 90%)"}
      - { label: "Tyr, God of Justice", value: "Tyr, God of Justice", color: "hsl(243, 95%, 90%)"}
      - { label: "Hermod, God of Luck", value: "Hermod, God of Luck", color: "hsl(347, 95%, 90%)"}
      - { label: "Bhaal, God of Terror and Hatrid", value: "Bhaal, God of Terror and Hatrid", color: "hsl(117, 95%, 90%)"}
      - { label: "Chauntea, Goddess of Agriculture", value: "Chauntea, Goddess of Agriculture", color: "hsl(224, 95%, 90%)"}
      - { label: "Dornia, Goddess of Knowledge", value: "Dornia, Goddess of Knowledge", color: "hsl(358, 95%, 90%)"}
      - { label: "Fharlanghn - God of Travel and Horizons", value: "Fharlanghn - God of Travel and Horizons", color: "hsl(254, 95%, 90%)"}
      - { label: "Talona, Goddess of Disease and Death", value: "Talona, Goddess of Disease and Death", color: "hsl(99, 95%, 90%)"}
      - { label: "Umbuso", value: "Umbuso", color: "hsl(346, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
      option_source: manual
  Pronounced:
    input: text
    accessor: Pronounced
    key: Pronounced
    label: Pronounced
    position: 7
    skipPersist: false
    accessorKey: Pronounced
    width: 190
    isHidden: false
    sortIndex: -1
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
      content_alignment: text-align-center
      content_vertical_alignment: align-middle
      wrap_content: true
  WhichParty:
    input: select
    accessor: WhichParty
    key: WhichParty
    label: WhichParty
    position: 16
    skipPersist: false
    accessorKey: WhichParty
    width: 138
    isHidden: false
    sortIndex: -1
    options:
      - { label: "The Adventurers", value: "The Adventurers", color: "hsl(152, 95%, 90%)"}
      - { label: "The New Adventurers", value: "The New Adventurers", color: "hsl(152, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
  Type:
    input: tags
    accessor: Type
    key: Type
    label: Type
    position: 9
    skipPersist: false
    accessorKey: Type
    width: 115
    isHidden: false
    sortIndex: -1
    options:
      - { label: "NPC", value: "NPC", color: "hsl(175, 95%, 90%)"}
      - { label: "VIP", value: "VIP", color: "hsl(38, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
  Sexuality:
    input: select
    accessorKey: Sexuality
    key: Sexuality
    label: Sexuality
    position: 11
    width: 150
    skipPersist: false
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Asexual", value: "Asexual", color: "hsl(36, 95%, 90%)"}
      - { label: "Bisexual", value: "Bisexual", color: "hsl(313, 95%, 90%)"}
      - { label: "Gay", value: "Gay", color: "hsl(235, 95%, 90%)"}
      - { label: "Straight", value: "Straight", color: "hsl(355, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
      source_data: current_folder
  SocialTrait:
    input: tags
    accessorKey: SocialTrait
    key: SocialTrait
    label: SocialTrait
    position: 21
    skipPersist: false
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Bossy", value: "Bossy", color: "hsl(115, 95%, 90%)"}
      - { label: "Cruel", value: "Cruel", color: "hsl(116, 95%, 90%)"}
      - { label: "Deferential", value: "Deferential", color: "hsl(325, 95%, 90%)"}
      - { label: "Demanding", value: "Demanding", color: "hsl(111, 95%, 90%)"}
      - { label: "Dependable", value: "Dependable", color: "hsl(217, 95%, 90%)"}
      - { label: "Dishonest", value: "Dishonest", color: "hsl(100, 95%, 90%)"}
      - { label: "Forthcoming", value: "Forthcoming", color: "hsl(110, 95%, 90%)"}
      - { label: "Friendly", value: "Friendly", color: "hsl(234, 95%, 90%)"}
      - { label: "Generous", value: "Generous", color: "hsl(297, 95%, 90%)"}
      - { label: "Helpful", value: "Helpful", color: "hsl(303, 95%, 90%)"}
      - { label: "Honest", value: "Honest", color: "hsl(145, 95%, 90%)"}
      - { label: "Impartial", value: "Impartial", color: "hsl(70, 95%, 90%)"}
      - { label: "Intolerant", value: "Intolerant", color: "hsl(136, 95%, 90%)"}
      - { label: "Lenient", value: "Lenient", color: "hsl(343, 95%, 90%)"}
      - { label: "Loyal", value: "Loyal", color: "hsl(280, 95%, 90%)"}
      - { label: "Peaceful", value: "Peaceful", color: "hsl(105, 95%, 90%)"}
      - { label: "Quite", value: "Quite", color: "hsl(218, 95%, 90%)"}
      - { label: "Secretive", value: "Secretive", color: "hsl(310, 95%, 90%)"}
      - { label: "Selfish", value: "Selfish", color: "hsl(70, 95%, 90%)"}
      - { label: "Selfless", value: "Selfless", color: "hsl(79, 95%, 90%)"}
      - { label: "Stingy", value: "Stingy", color: "hsl(129, 95%, 90%)"}
      - { label: "Suspicious", value: "Suspicious", color: "hsl(80, 95%, 90%)"}
      - { label: "Talkative", value: "Talkative", color: "hsl(198, 95%, 90%)"}
      - { label: "Tolerant", value: "Tolerant", color: "hsl(154, 95%, 90%)"}
      - { label: "Trusting", value: "Trusting", color: "hsl(207, 95%, 90%)"}
      - { label: "Uncooperative", value: "Uncooperative", color: "hsl(66, 95%, 90%)"}
      - { label: "Unfair", value: "Unfair", color: "hsl(176, 95%, 90%)"}
      - { label: "Unfaithful", value: "Unfaithful", color: "hsl(329, 95%, 90%)"}
      - { label: "Unfriendly", value: "Unfriendly", color: "hsl(37, 95%, 90%)"}
      - { label: "Unreliable", value: "Unreliable", color: "hsl(318, 95%, 90%)"}
      - { label: "Violent", value: "Violent", color: "hsl(124, 95%, 90%)"}
      - { label: "Unspeaking", value: "Unspeaking", color: "hsl(183, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
  AppearanceTrait:
    input: tags
    accessorKey: AppearanceTrait
    key: AppearanceTrait
    label: AppearanceTrait
    position: 22
    skipPersist: false
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Old", value: "Old", color: "hsl(115, 95%, 90%)"}
      - { label: "Disheveled", value: "Disheveled", color: "hsl(116, 95%, 90%)"}
      - { label: "Muscular", value: "Muscular", color: "hsl(325, 95%, 90%)"}
      - { label: "Menacing", value: "Menacing", color: "hsl(111, 95%, 90%)"}
      - { label: "Beautiful", value: "Beautiful", color: "hsl(217, 95%, 90%)"}
      - { label: "Small", value: "Small", color: "hsl(100, 95%, 90%)"}
      - { label: "Tall", value: "Tall", color: "hsl(110, 95%, 90%)"}
      - { label: "Ugly", value: "Ugly", color: "hsl(234, 95%, 90%)"}
      - { label: "Scarred", value: "Scarred", color: "hsl(297, 95%, 90%)"}
      - { label: "Hideous", value: "Hideous", color: "hsl(303, 95%, 90%)"}
      - { label: "Horrifying", value: "Horrifying", color: "hsl(145, 95%, 90%)"}
      - { label: "Posh", value: "Posh", color: "hsl(70, 95%, 90%)"}
      - { label: "Poor", value: "Poor", color: "hsl(136, 95%, 90%)"}
      - { label: "Attractive", value: "Attractive", color: "hsl(340, 95%, 90%)"}
      - { label: "Edgy", value: "Edgy", color: "hsl(62, 95%, 90%)"}
      - { label: "Thin", value: "Thin", color: "hsl(109, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
  MentalTrait:
    input: tags
    accessorKey: MentalTrait
    key: MentalTrait
    label: MentalTrait
    position: 23
    skipPersist: false
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Adaptive", value: "Adaptive", color: "hsl(346, 95%, 90%)"}
      - { label: "Ambitious", value: "Ambitious", color: "hsl(191, 95%, 90%)"}
      - { label: "Analytical", value: "Analytical", color: "hsl(124, 95%, 90%)"}
      - { label: "Cautious", value: "Cautious", color: "hsl(329, 95%, 90%)"}
      - { label: "Comformist", value: "Comformist", color: "hsl(73, 95%, 90%)"}
      - { label: "Complacent", value: "Complacent", color: "hsl(258, 95%, 90%)"}
      - { label: "Courageous", value: "Courageous", color: "hsl(53, 95%, 90%)"}
      - { label: "Cowardly", value: "Cowardly", color: "hsl(247, 95%, 90%)"}
      - { label: "Creative", value: "Creative", color: "hsl(96, 95%, 90%)"}
      - { label: "Decisive", value: "Decisive", color: "hsl(336, 95%, 90%)"}
      - { label: "Emotional", value: "Emotional", color: "hsl(212, 95%, 90%)"}
      - { label: "Impatient", value: "Impatient", color: "hsl(84, 95%, 90%)"}
      - { label: "Inattentive", value: "Inattentive", color: "hsl(281, 95%, 90%)"}
      - { label: "Incompetent", value: "Incompetent", color: "hsl(186, 95%, 90%)"}
      - { label: "Indecisive", value: "Indecisive", color: "hsl(270, 95%, 90%)"}
      - { label: "Independent", value: "Independent", color: "hsl(319, 95%, 90%)"}
      - { label: "Intelligent", value: "Intelligent", color: "hsl(66, 95%, 90%)"}
      - { label: "Patient", value: "Patient", color: "hsl(290, 95%, 90%)"}
      - { label: "Perceptive", value: "Perceptive", color: "hsl(21, 95%, 90%)"}
      - { label: "Reckless", value: "Reckless", color: "hsl(59, 95%, 90%)"}
      - { label: "Religious", value: "Religious", color: "hsl(279, 95%, 90%)"}
      - { label: "Secular", value: "Secular", color: "hsl(352, 95%, 90%)"}
      - { label: "Skeptical", value: "Skeptical", color: "hsl(11, 95%, 90%)"}
      - { label: "Skillful", value: "Skillful", color: "hsl(354, 95%, 90%)"}
      - { label: "Stupid", value: "Stupid", color: "hsl(315, 95%, 90%)"}
      - { label: "Superstitious", value: "Superstitious", color: "hsl(355, 95%, 90%)"}
      - { label: "Tenacious", value: "Tenacious", color: "hsl(195, 95%, 90%)"}
      - { label: "Uninventive", value: "Uninventive", color: "hsl(207, 95%, 90%)"}
      - { label: "Insane", value: "Insane", color: "hsl(345, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
  PersonalityTrait:
    input: tags
    accessorKey: PersonalityTrait
    key: PersonalityTrait
    label: PersonalityTrait
    position: 20
    skipPersist: false
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Anxious", value: "Anxious", color: "hsl(21, 95%, 90%)"}
      - { label: "Apathetic", value: "Apathetic", color: "hsl(38, 95%, 90%)"}
      - { label: "Articulate", value: "Articulate", color: "hsl(131, 95%, 90%)"}
      - { label: "Awkward", value: "Awkward", color: "hsl(278, 95%, 90%)"}
      - { label: "Calm", value: "Calm", color: "hsl(136, 95%, 90%)"}
      - { label: "Caring", value: "Caring", color: "hsl(196, 95%, 90%)"}
      - { label: "Charming", value: "Charming", color: "hsl(12, 95%, 90%)"}
      - { label: "Cheerful", value: "Cheerful", color: "hsl(293, 95%, 90%)"}
      - { label: "Childish", value: "Childish", color: "hsl(339, 95%, 90%)"}
      - { label: "Cold", value: "Cold", color: "hsl(266, 95%, 90%)"}
      - { label: "Depressed", value: "Depressed", color: "hsl(130, 95%, 90%)"}
      - { label: "Dull", value: "Dull", color: "hsl(248, 95%, 90%)"}
      - { label: "Eccentric", value: "Eccentric", color: "hsl(244, 95%, 90%)"}
      - { label: "Energetic", value: "Energetic", color: "hsl(74, 95%, 90%)"}
      - { label: "Enthusiastic", value: "Enthusiastic", color: "hsl(333, 95%, 90%)"}
      - { label: "Funny", value: "Funny", color: "hsl(205, 95%, 90%)"}
      - { label: "Gentle", value: "Gentle", color: "hsl(233, 95%, 90%)"}
      - { label: "Humble", value: "Humble", color: "hsl(197, 95%, 90%)"}
      - { label: "Humorless", value: "Humorless", color: "hsl(128, 95%, 90%)"}
      - { label: "Impolite", value: "Impolite", color: "hsl(67, 95%, 90%)"}
      - { label: "Incoherent", value: "Incoherent", color: "hsl(49, 95%, 90%)"}
      - { label: "Listless", value: "Listless", color: "hsl(127, 95%, 90%)"}
      - { label: "Mature", value: "Mature", color: "hsl(138, 95%, 90%)"}
      - { label: "Naive", value: "Naive", color: "hsl(320, 95%, 90%)"}
      - { label: "Optimistic", value: "Optimistic", color: "hsl(136, 95%, 90%)"}
      - { label: "Overt", value: "Overt", color: "hsl(187, 95%, 90%)"}
      - { label: "Pessimistic", value: "Pessimistic", color: "hsl(345, 95%, 90%)"}
      - { label: "Polite", value: "Polite", color: "hsl(251, 95%, 90%)"}
      - { label: "Proud", value: "Proud", color: "hsl(353, 95%, 90%)"}
      - { label: "Repulsive", value: "Repulsive", color: "hsl(77, 95%, 90%)"}
      - { label: "Respectful", value: "Respectful", color: "hsl(61, 95%, 90%)"}
      - { label: "Savvy", value: "Savvy", color: "hsl(85, 95%, 90%)"}
      - { label: "Sensitive", value: "Sensitive", color: "hsl(186, 95%, 90%)"}
      - { label: "Smooth", value: "Smooth", color: "hsl(81, 95%, 90%)"}
      - { label: "Subtle", value: "Subtle", color: "hsl(266, 95%, 90%)"}
      - { label: "Thick-skinned", value: "Thick-skinned", color: "hsl(69, 95%, 90%)"}
      - { label: "Wrathful", value: "Wrathful", color: "hsl(186, 95%, 90%)"}
      - { label: "Cunning", value: "Cunning", color: "hsl(332, 95%, 90%)"}
      - { label: "Confused", value: "Confused", color: "hsl(196, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
  Likes:
    input: text
    accessorKey: Likes
    key: Likes
    label: Likes
    position: 24
    skipPersist: false
    isHidden: false
    sortIndex: -1
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
  Dislikes:
    input: text
    accessorKey: Dislikes
    key: Dislikes
    label: Dislikes
    position: 25
    skipPersist: false
    isHidden: false
    width: 152
    sortIndex: -1
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
  Art:
    input: text
    accessorKey: Art
    key: Art
    id: Art
    label: Art
    position: 6
    skipPersist: false
    isHidden: false
    sortIndex: -1
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
      persist_formula: false
  Party1Standing:
    input: select
    accessorKey: Party1Standing
    key: Party1Standing
    id: PartyStanding
    label: Party1Standing
    position: 10
    skipPersist: false
    isHidden: false
    sortIndex: -1
    options:
      - { label: "Friend", value: "Friend", color: "hsl(243, 95%, 90%)"}
      - { label: "Family", value: "Family", color: "hsl(208, 95%, 90%)"}
      - { label: "Ally", value: "Ally", color: "hsl(91, 95%, 90%)"}
      - { label: "Enemy", value: "Enemy", color: "hsl(238, 95%, 90%)"}
      - { label: "Unmet", value: "Unmet", color: "hsl(108, 95%, 90%)"}
      - { label: "Acquaintance", value: "Acquaintance", color: "hsl(10, 95%, 90%)"}
      - { label: "Lover", value: "Lover", color: "hsl(337, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
  Pronouns:
    input: select
    accessorKey: Pronouns
    key: Pronouns
    id: Pronouns
    label: Pronouns
    position: 12
    skipPersist: false
    isHidden: false
    sortIndex: -1
    options:
      - { label: "He/Him", value: "He/Him", color: "hsl(111, 95%, 90%)"}
      - { label: "She/Her", value: "She/Her", color: "hsl(17, 95%, 90%)"}
      - { label: "They/Them", value: "They/Them", color: "hsl(187, 95%, 90%)"}
      - { label: "She/they", value: "She/they", color: "hsl(18, 95%, 90%)"}
      - { label: "Other", value: "Other", color: "hsl(151, 95%, 90%)"}
      - { label: "He/They", value: "He/They", color: "hsl(65, 95%, 90%)"}
      - { label: "Any", value: "Any", color: "hsl(184, 95%, 90%)"}
    config:
      enable_media_view: true
      link_alias_enabled: true
      media_width: 100
      media_height: 100
      isInline: false
      task_hide_completed: true
      footer_type: none
      persist_changes: false
config:
  enable_show_state: false
  group_folder_column: 
  remove_field_when_delete_column: true
  cell_size: compact
  sticky_first_column: true
  show_metadata_created: true
  show_metadata_modified: true
  source_data: current_folder
  source_form_result: root
  show_metadata_tasks: false
  frontmatter_quote_wrap: false
  row_templates_folder: /
  current_row_template: z._Templates/Template_-_NPC
  pagination_size: 15
  source_destination_path: /
  remove_empty_folders: false
  automatically_group_files: false
  hoist_files_with_empty_attributes: true
  show_metadata_inlinks: false
  show_metadata_outlinks: false
  enable_js_formulas: false
  formula_folder_path: /
  inline_default: false
  inline_new_position: top
  date_format: yyyy-MM-dd
  datetime_format: "yyyy-MM-dd HH:mm:ss"
  font_size: 16
  metadata_date_format: "yyyy-MM-dd HH:mm:ss"
  enable_footer: false
  implementation: default
  show_metadata_tags: false
filters:
  enabled: false
  conditions:
```