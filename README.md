# Concurrent Action Realm for Resource Iterations (CARRI)


Welcome to the **Concurrent Action Realm for Resource Iterations (CARRI)** project!

---

## Table of Contents

- [Abstract](#abstract)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Simulator](#running-the-simulator)
- [Constructing a Problem](#constructing-a-problem)
  - [Understanding `main.py`](#understanding-mainpy)
  - [Defining the Domain](#defining-the-domain)
  - [Implemented Domains](#implemented-domains)
-[Sample Problems](#sample-problems)
- [License](#license)
- [Contact](#contact)


---

## Abstract

The Concurrent Action Realm for Resource Iterations (CARRI) is a planning framework aimed at addressing multi-agent coordination, resource management, and adaptability in dynamic environments by combining classical planning techniques with a genetic algorithm. CARRI's modular design offers flexibility across a range of semi-structured problem domains, making it suitable for managing concurrent actions and iterative updates without being overly domain-specific. This README presents the architecture of CARRI and provides an evaluation of its genetic planning capabilities compared to other search-based approaches.

---

## Features

- **Dynamic Environment**: Simulate environments that can change over time, handling new requests and state changes.
- **Multi-Agent Support**: Plan for multiple agents with different capabilities and constraints.
- **Advanced Planning Algorithms**: Implement custom A* search and genetic algorithms for plan optimization.
- **Customizable Domains**: Define your own domains and problem instances using `.carri` files.
- **Action Simulation**: Generate valid actions and successors based on current states and constraints.
- **Modular Design**: Separate components for the simulator, problem definitions, state management, and planning algorithms.

---


---

## Getting Started

### Prerequisites

- Python 3.8 or later

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/dvicofirn/Concurrent-Action-Realm-for-Resource-Iterations.git


2. **Navigate to the Project Directory**
    ```bash
    cd Concurrent-Action-Realm-for-Resource-Iterations
    ```

## Running the Simulator
```bash
python CARRI/main.py
```

## Constructing a Problem
To construct a problem, you'll need to define both the domain and the problem instance. You can use main.py as a guide.

### Understanding main.py
The main.py script serves as the entry point for running simulations. It demonstrates how to set up the domain, problem, and initiate the planning algorithms.

Here's an outline of what main.py does:

- Defines the domain and problem files.
- Parses the domain and problem using Translator.
- Initializes the simulator with the parsed data.
- Sets up the model and planner.
- Runs the planning algorithm and outputs the plan.

### Defining the Domain
The domain file specifies the environment's entities, actions, and constraints.

for refrence look at the Examples directory. 

## Sample Problems
We created seven sample problems for the four implemented domains:

- Trucks and Drones 1: Simple problem with 5 iterations, 8 locations, 3 drones, and 2 trucks.
- Trucks and Drones 2: Extension of the first problem with more drones and trucks.
- Trucks and Drones 3: Complex problem inspired by New York City.
- Cars 1: Simple problem with 5 iterations, 3 cars, and 10 locations.
- Cars 2: Hard problem inspired by London’s sitemap.
- Motorcycles and Letters 1: Medium difficulty with dynamic elements.
- Rail System Factory 1: Medium difficulty with 9 iterations and 15 stations.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contact
For questions or feedback:

GitHub Repository: Concurrent-Action-Realm-for-Resource-Iterations

Authors:
Dvir Cohen - dvir.cohen@campus.technion.ac.il
Shir Turgeman - shirturgeman@campus.technion.ac.il
