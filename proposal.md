# Pokédex for Pokémon Go

## Overview

The number of Pokémon GO players has been steady since its launch in 2016 with almost 2 million daily active loyal users. The purpose of this app is to let players easily find out more information about pokémon types, moves, and statistics to optimize their gaming experience.

The user demographic will include:

- a wide range of age groups
- trainers located all over the world
- anyone who loves Pokémon!

## Data Sources

The main source of the data will be provided by the PokeApi which contains information about all the Pokémon that have ever existed, and this fan-created Pokémon Go API which contains only the Pokémon that exist in the mobile app version of the game.

## Database Schema

```py
class User(db.Model):
“””User.”””
**tablename** = “users”

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(254), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(50), nullable=True, unique=True)

    favorites = db.relationship('Favorite', backref='user', cascade="all, delete-orphan")

class Favorite(db.Model):
“””Favorites for user.”””
**tablename** = “users”

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    pokemon = db.Column(db.Text, nullable=False)
```

## Potential API Issues

Since the PokeAPI is free and fairly well-known, the only potential API issue would be figuring out the route for saving a user’s favorite pokemon. A challenge that may come up would be when creating a method for the models to favorite cards.

## Sensitive Information

- Encrypted passwords will be stored for the user model.
- An email address must be provided to identify a single user.
- Users do not need to enter first or last names, a username will be in place of this.

## Functionality

- Users can create their own accounts where they can set up basic information and have the option to edit or delete their account.
- Users can search for a pokémon or explore all the catchable pokémon on the Pokemon GO app.
- Upon clicking a result, there will be a page with more details about the pokémon such as: statistics, moves, strengths/weaknesses.
- Users can add and delete pokémon from their favorites which will be sorted by energy type.

## User Flow

- Landing/welcome page with a search bar.
- Anyone can browse through the site, however, if a user wants to save a pokémon to their favorites, they will need to create an account and be logged in.
- Logged in users can edit their profiles along with their favorites.

## Beyond CRUD

The CRUD aspect of the app revolves around the User and Favorite models for the ability to save a pokémon to a single page of favorites. The stretch goal is to have an on-screen, interactive pokedex where users are able to see their saved pokémon after they’ve created an account without having to refresh the page.

I may add an ability where players can use their current location or provide a location to pin a pokémon to the map using Leaflet that saves the coordinates, timestamp, and pokémon name to a database on the server, allowing other visitors to the site to view the pokémon’s last seen location go to the area that the pokémon was found in. users can use their current location or provide a location to pin a pokémon to the map.
