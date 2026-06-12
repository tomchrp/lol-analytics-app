# Référentiel des features à créer pour l'application



## Lane winrate : correction du winrate d'un matchup en exploitant les données à la fin de la phase de lane et non à la fin de la partie (on peut se faire int ou carry, on peut être bon ou mauvais sur un champion)

### Faisabilité : post game ou big data

### Biais :
- scaler, lane bully, champion early, support
- un roam peut faire perdre des golds sur la lane mais avoir un roi positif en prenant des kills ou debloquant un objectif
- biaisé par ganks ou jungler
### Features :
- comparaison des stats absolues et challenges entre les joueurs d'une lane à 14 minutes
- analyse des solo kills et kills avec participation d'un autre, voir si c'est jungler (on s'est fait gank ou on a joué un objectif, ou on a roam)
- analyse objectifs après kills et contexte des kills
- vérification positions joueurs à différentes frames pour analyser s'il y a eu lane swap
- intégrer participation aux kills ou position du jg/support adverse dans les events pour savoir si on a absorbé de la pression, ce qui explique une phase de lane a priori perdue



## Impact des wards : analyse de l'impact des wards sur la mort, la survie ou la prise d'un objectif

### Faisabilité : post game ou big data

### Biais : 
- aucune info dispo sur le placement exact des wards, il faut donc faire un proxy

### Features : 
- déduction d'une zone de ward à partir de l'évent et des frames précédentes et suivantes (pondéré par proximité temporelle, s'il y a 5s entre une frame et l'évent on ne prend que cette frame en compte)
- une fois la zone générée, calculer le placement des brushes dans la zone et déduire le brush de placement
- lie l'event ward aux events d'objectifs et de kills (utilise les event destruction de ward et objectifs pour déduire le placement (par ex dans le pit dragon))
- lier position jungler dans une frame aux placements de wards par des joueurs de ce coin de la map pour estimer ganks désamorcés ou permis grâce au manque de vision
- lier wards placées par un joueur à leur destruction (si beaucoup détruites, elles sont placées à des endroits pertinents)



## Rentabilité des ressources : golds générés et utilisés par rapport aux dégâts, soins et dégâts absorbés

### Faisabilité : post game ou big data

### Biais : 
- certains champions pokent mais ça ne mène pas à des kills (mais aussi à de la domination de lane donc ça peut être utile)
- assassins ont des dégâts burst mais pas sustained, donc potentiellement moins qu'un mage même s'ils sont plus utiles dans la game
- adapter la génération des golds à la lane et la classe

### Features : 
- rentabilité offensive (dmg)
- rentabilité défensive (tanking)
- rentabilité altruiste (supports)
- analyser event kill pour séparer les dégâts utiles du poke random
- regarder l'or en poche après un kill (en prenant en compte le shutdown) ou sa mort pour savoir si le joueur aurait pu être encore plus efficace



## Jungle diff : analyse de l'économie par rapport au jungler adverse

### Faisabilité : post game

### Biais :
- voler des camps c'est bien, mais moins impactant si le jg adverse prend un objectif ou un gank
- counter jungle en ultra late game n'est plus pertinent si tout le monde est full build (analyser la progression de l'économie, par exemple l'évolution des gold/min de chaque perso, et analyser le stuff en poche)
- dur de jouer les objectifs si les lanes se font gap (analyser events sur lanes et stats des lanes (or, items) avant prise d'un objectif pour définir faisabilité)
- certains jg sont utilitaires et d'autres veulent beaucoup de ressources (ivern vs khazix)

### Features : 
- analyse l'écart de ressources, d'objectifs et les camps volés au fil du temps
- analyse pose vision, kills et placement vision dans la frame avant la prise d'un objectif ou d'une tour (ou feature qui fait la même analyse avant un kill)
- comparer les actions suivant les frames de position des deux jg (l'un prend un kill tandis que l'autre a juste farm par exemple)



## Impact des achats : utilisation correcte des achats et impact sur la partie

### Faisabilité : post game ou big data

### Biais : 
- snowball avant l'achat
- analyse des composants, pas juste items complets (ex. serrated a plus d'impact en early que late sur un assassin)
- kill fait grâce à un niveau 6 qu'on vient de débloquer ou grâce à l'achat ?
- impact passif (zhonya pas compté mais ultra utile)

### Features :
- gold/stats diff à l'achat par rapport à son vis à vis
- utilisation des events de kill ou d'objectif pour voir les stats infligées après l'achat
- avantage de pression avec objectifs et bâtiments
- indice de parasitisme : toplaner qui farm mais prend pas d'objectifs, jungler qui prend les kills mais a peu de dmg
- adaptation à la game : achat de mr contre des ap
- croiser achat antiheal avec total heal de l'équipe ennemie pour voir si ça valait le coup ou non
- bon gameplay ou pas : un toplaner avec plein de solokills ou de kp mais pas de plates ou tours c'est bizarre
- itémisation correcte par rapport aux builds classiques du perso et à la draft d'en face (acheter item x est un blunder ? )



## Recommandateur d'items

### Faisabilité : obligé de dev un client pour récupérer les données pendant la draft

### Biais :
- faire du profiling big data pour connaître la répartition des types de dégâts infligés par les champions (certains ont des ratios ad sur des spells ap)
- analyser correctement spells et items : cleanse marche pas sur r malz mais qss oui
- attention aux flexpicks

### Features : 
- reco runes en croisant archétype et portée d'attaque : bone plating vs burst mêlée, second wind vs poke, unflinching vs hard cc
- reco items et bottes selon proportion dégâts adverses et archétype joué (on va pas faire dd si on joue un tank), pareil pour anti heal



## Créateur de builds off meta : feature fun avec query llm pour imposer un item ou une stat dans le build

### Faisabilité : maths sur stats des champions, query llm puis rag

### Biais : 
- coût des items, ordre de build (conseiller core avec rush car pas tout le temps complétable)
- anti synergie (runaan pas achetable sur mêlée)

### Features : 
- calcule proportion dégâts infligés par champions (big data) (certains spells sont ap mais ratio ad)
- étape 1 : traduction query llm en requête json avec stats, effets ou items imposés
- étape 2 : rag (reco items crit si crit ou item contenant crit demandé)
- étape 3 : solveur contraintes pour intégrer combinaisons et trouver la meilleure par rapport au champion (par exemple glisser des on hits si ça marche très bien sur le champ même si pas demandé)