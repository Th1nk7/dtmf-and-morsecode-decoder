# Morsecode and DTMF decoder
This is an exam project for programming.
The introduction and research question are made according to the requirements for this exam.

## Indledning
Jeg skal udvikle en webapp, der kan afkode morsekode og DTMF (Dual-Tone Multi-Frequency) fra en lydfil. Formålet med projektet er at gøre det muligt for brugere at uploade en lydfil med enten morsekode eller DTMF og få den dekodede tekst vist til brugeren.

Denne webapp kan være meget brugbar i flere sammenhæng. F.eks. vil den være god til CTF-konkurrencer, hvor der ofte er brug for netop disse funktioner.

Projektet vil gøre brug af lydanalyse, og til dette bruger jeg p5-sound, og de værktøjer den indholder. Analysen skal finde mønstre i lyden og dermed bestemme frekvenser for DTMF, eller længden af tonen for morsekode.

## Problemformulering
Hvordan kan jeg udvikle en webapp, hvor brugeren kan uploade en lydfil med enten morsekode eller DTMF, hvorefter lyden afkodes og den dekodede tekst vises til brugeren?

 - Hvordan kan man gøre det muligt at upload lydfiler?

 - Hvordan kan jeg finde forskellen mellem korte og lange signaler i morsekode?

 - Hvordan kan man finde frekvenserne, som skal bruges til DTMF?

 - Hvordan kan man afkode dataene og vise den korrekt.
