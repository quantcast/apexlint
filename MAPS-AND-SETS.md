Salesforce Apex Map and Set Guidelines
======================================

by Scott Posey and Simon Law

Copyright 2019 Quantcast Corporation


Summary
=======
**1. Avoid using mutable objects as Map keys or Set members.**

**2. Never mutate objects used as Map keys or Set members.**

Mutating Map keys or Set members
can cause their hashcode to change.

For Map keys, mutation can make the corresponding value inaccessible.
For Set members, mutation can make Set.contains(member) false.


SObject vs. Object hashcode and equals
======================================

**1. _Field values_ are used to compute SObject's hashCode
and equals.**

SObject hashcode and equals computation
_cannot_ be changed.

Although two SObjects
with the same field values
will have the same hashcode,
they will only be equals
if they are the same type.

**2. _Memory address_ (object identity) is the default implementation
for hashcode and equals for (non-SObject) custom classes.**

However, custom classes can (and should) override Object.hashCode() and Object.equals(),
and their implementations might also be sensitive to mutation like SObject.

Therefore any mutation of objects
can interfere with their behavior as Map keys or Set members.

Examples
========

        Account a = new Account(Name = 'Foo');

        // not recommended!
        Map<Account, String> stringsByAccounts = new Map<Account, String>();
        Set<Account> accountSet = new Set<Account>{};
        stringsByAccounts.put(a, 'Bar');
        accountSet.add(a);

        // things are OK as long as you don't mutate 'a'
        System.assertEquals('Bar', stringsByAccounts.get(a));
        System.assertEquals(true, accountSet.contains(a));

        // key mutation
        a.Name = 'Bar';

        // Map value inaccessible
        System.assertEquals(null, stringsByAccounts.get(a));

        // Set contains doesn't work
        System.assertEquals(false, accountSet.contains(a));

        // ... even though the it's still in the set
        System.assertEquals(1, accountSet.size());

        // if we flip back, everything works again!
        a.Name = 'Foo';
        System.assertEquals('Bar', stringsByAccounts.get(a));
        System.assertEquals(true, accountSet.contains(a));

        // 'a2' has the same field values as 'a'
        Account a2 = new Account(Name = 'Foo');

        System.assertEquals(a,a2);
        System.assertEquals(System.hashCode(a),System.hashCode(a2));

        // Maps and Sets can't distinguish 'a' vs 'a2'
        System.assertEquals('Bar', stringsByAccounts.get(a2));
        System.assert(accountSet.contains(a2));

        // putting a value for 'a2' into the map overwrites 'a' value 'Bar'
        stringsByAccounts.put(a2,'BarBar');
        System.assertEquals('BarBar', stringsByAccounts.get(a));


## Guidelines

1. **Map\<Object, V\> and Set\<Object\> are always flagged by the linter for review.**

    Objects should only be used
    as Map keys or Set members
    if they are not mutated.
    This pattern is only acceptable
    where the Map or Set
    is used within a single method.

    For SObjects,
    it's best if they are already in the database,
    since inserting them will assign an ID
    and therefore change their hashcode.

2. **Map<Id, SObject> must have the Id be of the same type as SObject.**

    This is to support the common pattern around:

       Map<Id, Account> m =
           new Map<Id, Account>(        
              [SELECT ID, Name from Account limit 10]);

     Or more generally, for `listofSobjects` which have been inserted:

         Map<Id, SObject> m =
             new Map<Id, SObject>(listOfSObjects);

     Obviously this doesn't work if the SObjects haven't been inserted, because their ids will all be null!

3. **Map<Id, T> is an anti-pattern where the types of Id and T do not match.**

    Either make it `Map<SObject, List<T>>`
    or `List<PairOfSObjectAndT>`.

4. **Map<Object, T> is also an anti-pattern if T isn't a container.**

    If there really is a 1:1 correlation,
    it's much safer to use Set<Object>
    and reference the T inside the Object.

5. **Map<T, U> behaves like Java if T is a user-defined class that does not implement equals and hashCode.**

    Values will be looked up
    using memory references for key objects.
    It's always preferable
    to implement equals and hashcode.

## Bypassing the Validation

If your code has been flagged
by the Apex Linter
and you'd like to bypass this validation
because you know what you're doing
and you have great confidence that
no one will ever call into your code the wrong way,
you can bypass the checker
by adding a reference to this document in a comment:

    Map<SObject, T> bad = new Map<SObject, T>(); // https://github.com/quantcast/apexlint/blob/master/MAPS-AND-SETS.md

### References

[Salesforce Maps Documentation](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_collections_maps.htm#heading_2_1)

[Salesforce: Using Custom Objects in Keys and Sets](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_collections_maps_keys_userdefined.htm?search_text=hashcode) : discussion of hashCode and equals

[Appirio: Considerations Using SObjects as Keys](https://hub.appirio.com/tech-blog/considerations-using-sobjects-in-sets-and-map-keys-in-apex) : third-party discussion of this issue
