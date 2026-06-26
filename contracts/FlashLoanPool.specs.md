# FlashLoanPool - User Stories

## Objectif
Permettre des flash loans non-collateralises, avec remboursement dans la meme transaction et frais de pret ajustes par le proprietaire.

## User stories
- En tant que fournisseur de liquidite, je veux deposer de l'ETH afin d'augmenter la capacite de flash loan du pool.
- En tant que fournisseur de liquidite, je veux retirer mes parts afin de recuperer mon capital disponible.
- En tant qu'emprunteur flash loan, je veux emprunter temporairement de l'ETH afin d'executer une strategie atomique.
- En tant qu'emprunteur flash loan, je veux recevoir une verification de callback afin de confirmer que mon contrat respecte le protocole.
- En tant que proprietaire, je veux modifier les frais afin d'ajuster la rentabilite du pool.
- En tant que proprietaire, je veux blacklister certains contrats afin d'empecher des usages abuses.
- En tant que proprietaire, je veux mettre le pool en pause afin de suspendre les operations en cas d'incident.
- En tant que proprietaire, je veux recuperer les frais accumules afin de monetiser l'activite du pool.

## Critres d'acceptation
- Un flash loan ne peut pas exceder `MAX_LOAN_PERCENT` de la liquidite totale.
- Le receiver doit renvoyer `CALLBACK_SUCCESS` depuis `onFlashLoan`.
- Le solde final du pool doit etre au moins egal au solde initial plus les frais attendus.
- Les emprunteurs blacklists sont refuses.
- Les operations de depot respectent l'etat de pause.
- Les evenements `Deposited`, `Withdrawn`, `FlashLoan`, `FeeUpdated` et `Blacklisted` doivent etre emis quand approprie.

## Parcours utilisateur
1. Un fournisseur depose de la liquidite.
2. Un contrat receiver demande un flash loan.
3. Le contrat execute sa logique puis rembourse le principal et les frais dans le meme appel.
4. Le pool verifie le callback et enregistre les frais collectes.