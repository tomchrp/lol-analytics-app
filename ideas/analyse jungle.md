# Feature : 
- counter jungle : que fait un jungler quand l'autre déclenche un event, ou pendant une frame, et vice versa, calculer delta de camps tués entre chaque frame et croiser avec position et challenge camps volés pour faire un proxy de l'invade
- pression fantôme : croiser les positions des junglers avec celles des laners lors des events et frames : si un jungler passe du temps vers une lane, n'intervient pas mais que le laner perd de l'xp, on peut admettre une pression imposée par le jg
- efficacité des ganks : identifier l'investissement d'un gank avec un proxy du farm perdu et temps hors jungle * or moyen perdu, regarder la position du jg dans les deux frames entourant l'event
- écart de ressources : à partir des frames et challenges, extraire les stats, le stuff et l'xp des junglers, proxy des camps volés
- setup vision avant kill ou objectif : entourer un event avec les frames et faire un proxy space time
- action post frame ou post event 
- cross map play : si A prend un dragon, B avait pour choix de : ne pas farm du tout, farm ses propres camps, invade, prendre un kill ou un objectif quelque part
- or dormant : regarder l'or, les stats et les items en poche dans la frame précédant un event pour déterminer un avantage statistique et des dépenses nécessaires
- clutch factor : classer chaque objectif comme free, contesté ou volé, utiliser clés epicMonsterSteals et epicMonsterKillsNearEnemyEnemy de challenges post game en croisant avec le plus d'ennemis à proximité
- wave management : différencier fix ou taxe wave en regardant l'évolution des minionsKilled (acceptable si c'est après un kill ou s'il n'y a personne sur cette lane (biais potentiel : laner est à la base ou en cours de chemin))
- renta golds : regarder le ratio dmg/gold ou cc ou heal/gold (attention aux persos low dps mais high burst)
- contrôle river : scuttleCrabKills et position frames proches
- profil jungler : damageDealtToObjectives, damageDealtToTurrets, totalDamageDealtToChampions pour établir un profil carry, macro, etc.
- efficacité early : jungleCsBefore10Minutes, takedownsFirstXMinutes, maxKillDeficit
- snowball : analyse de la kp au fur et à mesure du match


# Sources données : Match v5
## timeline_vents : 
- WARD_PLACED
- ITEM_PURCHASED (qui achète un item avant l'autre)
- CHAMPION_KILL
- CHAMPION_SPECIAL_KILL
- TURRET_PLATE_DESTROYED
- ELITE_MONSTER_KILL
- WARD_KILL
- DRAGON_SOUL_GIVEN
- BUILDING_KILL
- LEVEL_UP
- SKILL_LEVEL_UP
- CHAMPION_TRANSFORM (pour kayn)
- OBJECTIVE_BOUNTY_PRESTART & OBJECTIVE_BOUNTY_FINISH
- ITEM_UNDO
- ITEM_SOLD

## timeline_frames :
- 

## match_details (challenges) : 
- acesBefore15Minutes 
- alliedJungleMonsterKills
- baronBuffGoldAdvantageOverThreshold
- baronTakedowns
- bountyGold
- buffsStolen
- damagePerMinute
- damageTakenOnTeamPercentage
- earliestBaron
- earlyLaningPhaseGoldExpAdvantage
- effectiveHealAndShielding
- elderDragonKillsWithOpposingSoul
- elderDragonMultikills
- enemyJungleMonsterKills
- epicMonsterKillsNearEnemyJungler
- epicMonsterKillsWithin30SecondsOfSpawn
- epicMonsterSteals
- epicMonsterStolenWithoutSmite
- firstTurretKilled
- getTakedownsInAllLanesEarlyJungleAsLaner
- goldPerMinute
- initialCrabCount
- initialBuffCount
- jungleCsBefore10Minutes
- junglerTakedownsNearDamagedEpicMonster
- kTurretsDestroyedBeforePlatesFall
- kda
- killParticipation
- killsNearEnemyTurret
- maxKillDeficit
- maxLevelLeadLaneOpponent
- moreEnemyJungleThanOpponent
- multiTurretRiftHeraldCount
- outnumberedKills
- perfectDragonSoulsTaken
- scuttleCrabKills
- soloBaronKills
- soloKills
- takedowns
- takedownsAfterGainingLevelAdvantage
- takedownsBeforeJungleMinionSpawn
- takedownsFirstXMinutes
- teamDamagePercentage
- visionScoreAdvantageLaneOpponent
- visionScorePerMinute
- wardTakedowns
- earliestDragonTakedown
- junglerKillsEarlyJungle
- killsOnLanersEarlyJungleAsJungler
- controlWardTimeCoverageInRiverOrEnemyHalf
- teleportTakedowns
- 
- 
 
# Points de friction : 
- pas d'info sur les positions des wards, il faut faire un proxy
- les events ne contiennent pas les stats des joueurs mais elles sont nécessaires (stockées dans les frames)

# Biais : 
- archétype jungler (farm vs carry vs utility...)
- faisabilité des objectifs (si l'ennemi (avec ou sans jg) vient de prendre une tour ou un kill, on n'a pas de prio sur l'objectif)
- attention aux shutdowns pour la valeur des kills et objectifs
- voler des camps c'est bien, mais moins impactant si le jg adverse prend un objectif ou un gank
- counter jungle en ultra late game n'est plus pertinent si tout le monde est full build (analyser la progression de l'économie, par exemple l'évolution des gold/min de chaque perso, et analyser le stuff en poche)
- dur de jouer les objectifs si les lanes se font gap (analyser events sur lanes et stats des lanes (or, items) avant prise d'un objectif pour définir faisabilité)
- certains jg sont utilitaires et d'autres veulent beaucoup de ressources (ivern vs khazix)

# Pyramide de données : 
- Niveau 1 : bilan absolu et descriptif (KDA, golds, vision, dmg)
- Niveau 2 : Scores de maîtrise (radar) : contrôle de river, efficacité ganks...
- Niveau 3 : diagnostic intelligent

- Coût d'opportunité : golds manqués ou générés grâce ou à cause d'une action

- Niveau 3 : analyse des turning points (kill ou objectif) -> aspire les frames et events autour de la clé pour définir une séquence de jeu -> frise temporelle avec carte de séquences


### Etape 1 : définition des ancres : 
- Majeure : objectif ou bâtiment
- Mineure : kill ou plate

### Etape 2 : fenêtrage : 
- définition d'un rayon d'attraction temporelle (+-X secondes)
- extraction de tous les events et frames dans ce laps de temps

### Etape 3 : fusion des chevauchements
- si un kill arrive à 14:30 et un drake à 15:00, on fait une séquence de 14:00 à 16:00

### Etape 4 : étiquetage
- Scenario A : kill -> objectif : fight pour setup drake
- Scenario B : objectif -> kill : exploitation de l'objectif pour teamfight
- Scenario C : echec (mort jg allié puis drake ennemi) : perte d'objectif suite à erreur

- Séparation correcte des events en analysant la position : une tour prise au top et un drake dans les 30s sont deux séquences différentes, il faut assigner les acteur et les events à la bonne séquence
- Prendre aussi en compte les déplacements rapides avec position à frame et event (tp, ulti tf, recall, etc.) ou les interventions remote (ulti jinx -> analyse position participants à un kill à la frame la plus proche) 

# Outils multi parties : 
- radar de profil : carry, soutien, contrôleur... avec axes (invade, efficacité, contrôle) et superposition aux average de l'elo
- heatmap position par frame ou tranche de 5 minutes ou autour d'un event (par exemple heatmap autour du premier drake (donc pas lié à un timer exact vu que ça change) pour évaluer setup objectif ou pathings)
- diagramme flux qui montre les X premières minutes pour avoir une idée du start
- matrice d'adversité : comment est-ce qu'on performe face à un farming jungler ou un early invader ?

# Outils partie unique : 
- graphe or total vs or dépensé pour voir la dead money
- scatter plot effort récompense avec temps investi en X et valeur extraite en Y : points en bas à droite sont de mauvais ganks qui font perdre du temps
- diagramme entonnoir avec ratios conversion : sur 5 ganks réussis, 3 ont mené à une prise de vision profonde, 1 a mené à un objectif
- graphique cascade des swings de partie : barres positives ou négatives pour quantifier l'impact financier d'une séquence du moteur timeline
- allocation ressources : assistances = dons, taxes = siphon pour ses carrys potentiels