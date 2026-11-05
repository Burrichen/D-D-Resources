---
id: creature/korthalax
type: creature
name: Korthalax
aliases: [Korthalax Umbuso]
summary: Huge, angered Umbuso predator (CR 14) from a v2 planning statblock; no lore written yet.
tags: [umbuso, hundred-gods, statblock]
related: [lore/umbuso]
status: draft
sources:
  - {source: obsidian-dnd-v2, path: "Umbuso Planning Room.md", hash: "sha256:b4c8a4bfd16e3d7c3a5a0a599ab21580521fc9813cdd760ad07630ad69c4ccb0", role: primary}
licence: own-work
updated: 2026-11-04
classification: Umbuso
creature_type: Ancient Creature
cr: '14'
---

A Huge, angered [Umbuso](/content/lore/umbuso.md) built as a boss statblock in the v2 "Umbuso Planning Room". There is no archive entry or lore for it yet.

## Statblock

```statblock
layout: Basic 5e Layout
image: 
name: Korthalax Umbuso
size: Huge
type: Ancient Creature
subtype: angered
alignment: Chaotic Neutral
ac: 19
hp: 200
hit_dice: 18d12 + 90
speed: 35 ft
stats: [26, 14, 22, 5, 16, 8]
saves:
  - Str: 14
  - Con: 12
  - Wis: 9
skillsaves:
  - perception: 9 
  - intimidation: 5
  - Stealth: 8
damage_resistances: poison, bludgeoning, piercing, and slashing from nonmagical attacks
condition_immunities: frightened, poisoned, grappled, shove
senses: tremorsense 120ft., darkvision 120ft., pPerception 19
languages: none
cr: 14
traits:
  - name: Apex Predator
    desc: When Korthalax falls below half its hit points, it gains 2 additional Legendary Actions each round. It also shakes off all grapples and CC.
  - name: Titanic Resilience
    desc: Korthalax ignores all magical damage under 15. The first time per combat it drops below half its hit points, it gaints 20 temporary hit points.
actions:
  - name: Multiattack
    desc: One Bite, two claws
  - name: Bite
    desc: "+11 to hit, reach 10ft. 2d10 + 5 piercing, DC 16 strength or grappled in mouth."
  - name: Claw
    desc: +11 to hit, reach 5 ft., 1d8 + 6 slashing.
  - name: Tail Sweep
    desc: 30 ft., arc tail sweep. Each creature must succeed a DC 17 dex save or take 4d8 and knocked prone
  - name: Swallow
    desc: If a creature is still grappled, get swallowed.
  - name: Korthalax Scream (1d4 + 2 recharge)
    desc: Summon 3 dire wolves as its children.
legendary_actions:
  - name: Legendary Pool 
    desc: 3 legendary actions each turn.
  - name: Transcluence
    desc: The animal turns transluent. The first attack against the creature this turn has disadvantage
  - name: Tail Smash
    desc: One creature within 15. must succeed on a DC 16 Str save or take 2d8 + 4 bludgeoning damage and be knocked prone.
  - name: Roaring Challenge (2 actions)
    desc: One creature, Korthalax can see within 30 ft. must succeed on a DC 17 Wisdom save or be frightened until the end of next turn.
bonus_actions:
  - name: 
    desc: 
  - name: 
    desc: 
reactions:
  - name: 
    desc: 
  - name: 
    desc: 
```

## GM notes

- Planning notes on the v2 page: "Cr cap -1" and "3 x 5 = 15 cap".
- The statblock's bonus-action and reaction slots are empty.
- The v2 Act III plan has the party sent on an "Umbuso hunt (boss fight)" in the rainforest, after powerful people destroying it anger the local Umbuso. Session 19's "The Umbuso" section is empty. It isn't confirmed that this is Korthalax.
