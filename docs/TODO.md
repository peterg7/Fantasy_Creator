# Fantast Creator TODO

## Tree

### Tree

- Completed initial round of organizing file and commenting 

- Remove new tree that is created from an offspring (give option of which family to join; one of the parents families)

- Implement new tree strategy (at most 2 instances of any character) -> develop on clean book

  - Situation 1: two end point heads of family
    - [ ] Adding child to family with two null parents
    - Base case, make solid

  - Situation 2: one terminating head of family, one with parents
    - [ ] Adding child to existing family
    - [ ] Adding a partner to one of the families children
    - Need to clone the added child. It will exist in the partnered family and it's own
  - Situation 3: two joined families
    - [ ] Creating a partnership between children in two different families
    - Need to clone both children. They will both exist in each family
  - Situation 4: new family from children partners
    - [ ] Joining two families by their children and spawning their children
    - Need to clone both children serving as parents and their offspring. The new "family" will not have its own tree but exist in each of the children's original families

### Character

### Family

- Need a way to not remake the entire graph + tree when updated

### Partners



## Timeline



## Map



## Scroll



## Preferences

- Figure out better way to share preferences instead of in the database

## Animation



## Mechanics

- Offload some of the database to disc so it doesn't overload RAM

## General



## UI

- Maybe center the tabs on the window?