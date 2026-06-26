# StakingToken - User Stories

## Objectif
Permettre a des utilisateurs de detenir, transferer, staker et retirer un token ERC20 simplifie avec recompenses par bloc et penalite de sortie anticipee.

## User stories
- En tant que detenteur de tokens, je veux transferer mes jetons a un autre compte pour gerer librement mon solde.
- En tant que detenteur de tokens, je veux approuver un tiers pour depenser mes jetons afin de permettre des operations de type `transferFrom`.
- En tant qu'utilisateur, je veux staker mes jetons pour generer des recompenses afin de faire fructifier mon solde.
- En tant qu'utilisateur, je veux voir mes recompenses en attente afin de savoir combien je vais recevoir si je retire maintenant.
- En tant qu'utilisateur, je veux retirer mes jetons staked afin de recuperer ma liquidite quand je le souhaite.
- En tant qu'utilisateur qui retire trop tot, je veux accepter une penalite afin de respecter la regle de blocage minimum.
- En tant que proprietaire, je veux minter de nouveaux jetons afin d'alimenter le systeme ou distribuer des jetons supplementaires.

## Critres d'acceptation
- Un stake de montant nul est refuse.
- Un compte ne peut pas staker plus de jetons qu'il n'en possede.
- Les recompenses s'accumulent selon `REWARD_RATE` et sont distribuees au fil des blocs.
- Un retrait avant `MIN_STAKE_BLOCKS` applique `EARLY_WITHDRAWAL_PENALTY`.
- Les fonctions `transfer`, `approve`, `transferFrom`, `stake` et `unstake` emettent les evenements attendus.

## Parcours utilisateur
1. L'utilisateur recoit des jetons.
2. Il stake une partie de son solde.
3. Le temps passe et les recompenses s'accumulent.
4. Il retire tout ou partie de son stake.
5. Le contrat applique ou non une penalite selon la duree de detention.