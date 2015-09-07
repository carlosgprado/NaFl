NaFl
====


FAQ
---

- Why _NaFl_?
    - _NaFl_ means sarcastically: "It is totally Not AFL" </sarcasm>
    - NOTE: when I say AFL, I mean AFL v.0.1 alpha ;)
- What is it?
    - It is a prototype of a _code coverage fuzzer_. I wanted to have something like [AFL](http://lcamtuf.coredump.cx/afl/) to use in Windows. Unfortunately everything looked very *NIX centric (AFAIK) so I decided to implement the _core principles_ from the ground up (and learned something on the way)
    
    - It leverages dynamic binary instrumentation (DBI) to measure code coverage in blackbox Windows binaries.
        - "Fun" fact: adding support for Intel PIN to AFL was actually my original research project but _mothran_ beat me to it, see his (her?) fantastic work [here](https://github.com/mothran/aflpin)
        - _NaFl_ can be thought as this with some Python core implementing a simple fuzzing logic

- Why does the code suck so much?
    - Don't let physicists do computer science. Or anything else for that matter :)


## Installation ##

_NaFl_ is written in Python (Core) and C/C++ (the DBI core).
Most of the installation is straightforward:

- Clone the project
- There are two major directories:
    - NaFlCore: nothing to do here at installation time
    - PinTool: contains a single file "MyPinTool.cpp"
    - Compiling your own PinTool is kind of a pain so most of the people I know use this little trick:
        - _cd_ to _Pin_directory_\source\tools\MyPinTool
        - Overwrite the _MyPinTool.cpp_ file with yours
        - Open the project in Visual Studio (I used VS Community 2013, very recommended to use this one)
        - Build the project
            - NOTE: if you get errors complaining about SafeSEH just deactivate it in the linker options.
            - Right click -> Properties -> Configuration Properties -> Linker -> All Options
            - Search for "_Image Has Safe Exception Handlers_" and set it to "_NO (/SAFESEH: NO)_"
        - Move the resulting DLL to a directory of your choice (you can rename it as well)

- That should do it.


### Dependencies ###

- Python 2.7.x (grab it [here](https://www.python.org/downloads))
    - Recommended Python 2.7.9+ (includes pip)

- Intel PIN (download it [here](http://software.intel.com/sites/landingpage/pintool/downloads/pin-2.14-71313-msvc12-windows.zip))

These Python modules are part of the client's core:

- Winappdbg (pip install winappdbg)
    - This is awesome sauce, check more [here](http://winappdbg.sourceforge.net/)
- SQLAlchemy (pip install sqlalchemy)

The following Python modules are needed for the server:

- Tornado (pip install tornado)
- Twisted (pip install twisted)


### Running ###

Once currently installed, running is pretty straightforward.

- Run the server for collecting information and crash files
    - python server\xmlrpc-server.py

- Edit the config file
    - Location of PIN and the corresponding PinTool
    - Location of the ~~victim~~ binary to analyze

- Run the core
    - python NaFlCore.py


### Future Enhancements ###

__SO MANY…__

- Plugin system
    - Pre- & Post- processing of the mutation
    - Unzip / Zip for formats like DOCX and alike
    - Decrypt / Encrypt...
    - etc.

- Static analysis of the victim binary itself
    - Cannibalize strings
    - Check proximity to str(n)cmp and alike…
        - Maybe implement in [JARVIS](https://github.com/carlosgprado/JARVIS)?

- Analysis of the samples
    - Find high entropy regions (uninteresting)
    - Find ASCII regions
    - Compare samples to find fixed tokens (PNG, etc.)

- Regularly evaluate the quality of mutations in the queue
    - Remove ones not yielding anything interesting in a long time?
    - Trim mutations?


### Thanks ###

This was done during my work time and therefore paid by my current employer, [Siemens AG](http://www.siemens.com) 

__Yes we do more than washing machines! ;)__

Thanks for allowing this public release.
