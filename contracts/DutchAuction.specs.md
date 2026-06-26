# DutchAuction - User Stories

## Objectif
Permettre de vendre un lot de tokens via une enchere hollandaise dont le prix baisse avec le temps jusqu'au reserve price.

## User stories
- En tant que vendeur, je veux lancer une enchere avec un prix de depart, un prix reserve et une duree afin de definir les conditions de vente.
- En tant qu'acheteur, je veux connaitre le prix courant afin de decider quand enchere.
- En tant qu'acheteur, je veux acheter une quantite de tokens pendant la fenetre active afin de participer a la vente.
- En tant qu'acheteur, je veux recuperer le trop-percu si je paie plus que le cout exact afin de ne pas surpayer.
- En tant que vendeur, je veux finaliser l'enchere afin de declencher le calcul des remboursements et des produits.
- En tant qu'acheteur, je veux reclamer mon remboursement si le prix de clearing est plus bas que le prix que j'ai paye.
- En tant que vendeur, je veux retirer les fonds apres settlement afin de recuperer les produits de la vente.
- En tant que vendeur, je veux proteger la vente avec une whitelist optionnelle afin de limiter l'acces a certains acheteurs.

## Critres d'acceptation
- Le prix de depart doit etre strictement superieur au prix reserve.
- Une enchere ne peut etre placee que pendant la periode active et avant le settlement.
- Les achats ne peuvent pas depasser `totalSupply`.
- Le settlement calcule le prix de clearing puis credite les remboursements eventuels.
- Le retrait du vendeur n'est possible qu'apres settlement.
- Les evenements `BidPlaced`, `AuctionSettled`, `Refunded` et `Withdrawn` doivent etre emis.

## Parcours utilisateur
1. Le vendeur initialise l'enchere.
2. Les acheteurs placent des bids pendant la baisse de prix.
3. L'enchere est settlee quand la quantite totale est atteinte ou a la fin de la duree.
4. Les remboursements sont reclames si necessaire.
5. Le vendeur retire les produits.