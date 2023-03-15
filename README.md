# ChemIndex
#### Video Demo:  https://youtu.be/QKbW_OlpfEs

#### Description:
  
Chemical management app designed for academic and commercial laboratories. This app has three main functions.

Firstly, you can search for the unique identifier for any chemical, known as the CAS Registry Number, from any of its possible names using an API request from commonchemistry.cas.org. The obtained data is saved to a SQL database, which can be viewed in a tabulated layout in the app. You can also search through the table for a chemical using JavaScript. The app also features a submodule from GitHub that allows you to further search for the Safety Data Sheet (SDS) of any chemical, which is required when using any chemical in a laboratory.

Secondly, you can make stock buy requests for any chemical in the CAS database, including details such as required quantities and urgency of order. The app places the request into an order log (SQL database), which can be viewed as a table, and the managerial staff can purchase the chemical directly from the data table by clicking a button.

Thirdly, the app provides a comprehensive stock management system. After the managerial staff purchases any stock, it is added to the chemical's overall stock count, which is derived from a SQL database query. The app includes a function to deduct the relevant amount of stock from the stock database upon using up an 'amount' of any stock, and the running total is updated. The overall stock can be searched and viewed at any time. The app can handle unit conversions in the backend for you, making it convenient to purchase or remove stock using appropriate units.

The databases that can be viewed in the application include the CAS Registry database, Order Log Database, and Stock Removal Log Database. This app is a comprehensive solution to manage and track chemicals in any laboratory. 


Tech stack used in creation of this project: Python, Flask, SQL, html, CSS, Javascript, Bootstrap, jinja templating tools.
