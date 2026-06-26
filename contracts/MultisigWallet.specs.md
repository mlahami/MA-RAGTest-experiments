# MultisigWallet - User Stories

## Objectif
Permettre a plusieurs signataires de proposer, confirmer et executer des transactions soumises a un quorum et a un delai de securite.

## User stories
- En tant que signataire, je veux proposer une transaction afin de soumettre une action a la validation du groupe.
- En tant que signataire, je veux confirmer une transaction afin de contribuer au quorum.
- En tant que signataire, je veux retirer ma confirmation avant execution afin de corriger une decision.
- En tant que signataire, je veux executer une transaction valide afin de faire avancer les operations de la multisig.
- En tant que membre du systeme, je veux que les executions soient soumises a un timelock afin de laisser le temps au groupe de reagir.
- En tant que contrat lui-meme, je veux pouvoir annuler une transaction afin de bloquer une operation devenue invalide.
- En tant que gestionnaire de gouvernance interne, je veux ajouter ou retirer des signataires afin d'adapter la composition du groupe.
- En tant que gestionnaire de gouvernance interne, je veux modifier le quorum afin d'ajuster le niveau de securite.

## Critres d'acceptation
- Une proposition doit contenir une adresse cible valide.
- Seuls les signataires peuvent proposer, confirmer, revoker ou executer.
- Une transaction ne peut etre executee que si le quorum est atteint et si `TIMELOCK_DELAY` est passe.
- Une transaction ne peut pas etre executee deux fois.
- La suppression d'un signataire ne doit pas casser le quorum.
- Les evenements `Proposed`, `Confirmed`, `Revoked`, `Executed`, `Cancelled`, `SignerAdded`, `SignerRemoved` et `QuorumChanged` doivent etre emis.

## Parcours utilisateur
1. Un signataire propose une action.
2. Plusieurs signataires confirment.
3. Le timelock expire.
4. La transaction est executee depuis le contrat lui-meme.
5. Les modifications de gouvernance passent par le mecanisme interne `onlyThis`.