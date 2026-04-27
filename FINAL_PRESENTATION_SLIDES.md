# ITMD 422/523 Final Project Presentation

## Slide 1. Title

**Institutional Trader Portfolio Management System**

- Course: ITMD 422/523 Final Project
- Team members: [Add names here]
- DBMS: MySQL
- Application type: Web-based portfolio management system

## Slide 2. Problem and Goal

**Problem**

- Portfolio and trading information is spread across multiple business entities
- Users need a simple interface to view holdings, record trades, and monitor limits
- Database operations should happen through the application, not manual SQL tools

**Goal**

- Build a working web application with a MySQL backend
- Support core business workflows
- Demonstrate select, insert, update, and delete through user interaction

## Slide 3. System Overview

- Frontend: HTML/CSS/JavaScript
- Backend: FastAPI
- Database: MySQL
- Deployment: Theta EdgeCloud HTTP endpoint
- Main modules: Dashboard, Holdings, Transactions, Risk, Trading, Master Data, Users

## Slide 4. Database Design

**Core tables**

- `Traders`
- `Counterparties`
- `Assets`
- `Accounts`
- `Transactions`
- `Holdings`
- `Risk_Limits`
- `Users`

## Slide 5. ERD / Relationship Summary

- One trader can manage many accounts
- One account can have many transactions
- One asset can appear in many transactions and holdings
- One counterparty can be linked to many transactions
- One account can have many risk limits
- Foreign keys maintain entity relationships

## Slide 6. Business Function 1

**Portfolio Monitoring**

- Portfolio summary by account
- Holdings by account
- Exposure by asset class
- Unrealized and realized P&L

## Slide 7. Business Function 2

**Trade and Risk Management**

- Create new transactions
- Amend or cancel transactions
- Add and modify risk limits
- Monitor alerts and breaches

## Slide 8. CRUD Requirement Mapping

- Select / Query: dashboard, holdings, transactions, risk alerts, master data
- Insert: add trade, add asset, add account, add counterparty, add user, add risk limit
- Update: edit user, update risk limit, amend transaction, update asset price
- Delete: cancel transaction, close account, delist asset, deactivate counterparty, deactivate risk limit, delete user

## Slide 9. Demo Plan

1. Log in to the system
2. Show dashboard and holdings
3. Insert a new trade
4. Show updated transactions and holdings
5. Update a risk limit
6. Cancel a transaction
7. Show master data CRUD if time allows

## Slide 10. Key Screens

- Login page
- Dashboard
- Transactions page
- Risk monitor
- Trading interface
- Master data management

## Slide 11. Implementation Highlights

- MySQL schema and seed data
- FastAPI CRUD APIs
- Responsive web UI
- JWT login
- Portfolio, transaction, and risk workflows
- Recent fixes for demo stability and UI polish

## Slide 12. Challenges and Solutions

**Challenge**

- Keeping UI actions aligned with backend/database rules

**Solution**

- Matched trading UI values to database enums
- Fixed transaction and risk modal loading
- Improved routing and local frontend serving

## Slide 13. Conclusion

- Complete MySQL-backed database application
- At least 2 business functions
- Full CRUD through the interface
- Realistic scope for the course final project

## Slide 14. Contribution Statement

- Student A: database design, schema creation, SQL queries
- Student B: frontend UI and backend integration
- Student C: testing, debugging, deployment, slides, and demo preparation

Replace with your real team information before submission.
