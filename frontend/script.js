document.getElementById('fetchUsers').addEventListener('click', fetchUsers);
document.getElementById('fetchProducts').addEventListener('click', fetchProducts);

async function fetchUsers() {
    const usersList = document.getElementById('usersList');
    usersList.innerHTML = '<li>Loading users...</li>';
    try {
        const response = await fetch('/proxy/users_service/users/'); 
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
        }
        const users = await response.json();
        usersList.innerHTML = ''; 
        if (users.length === 0) {
            usersList.innerHTML = '<li>No users found.</li>';
            return;
        }
        users.forEach(user => {
            const li = document.createElement('li');
            li.textContent = `ID: ${user.id}, Username: ${user.username}, Email: ${user.email}`;
            usersList.appendChild(li);
        });
    } catch (error) {
        console.error('Error fetching users:', error);
        usersList.innerHTML = `<li>Error fetching users: ${error.message}</li>`;
    }
}

async function fetchProducts() {
    const productsList = document.getElementById('productsList');
    productsList.innerHTML = '<li>Loading products...</li>';
    try {
        const response = await fetch('/proxy/products_service/products/'); 
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
        }
        const products = await response.json();
        productsList.innerHTML = '';
        if (products.length === 0) {
            productsList.innerHTML = '<li>No products found.</li>';
            return;
        }
        products.forEach(product => {
            const li = document.createElement('li');
            li.textContent = `ID: ${product.id}, Name: ${product.name}, Price: $${product.price}, Stock: ${product.stock_quantity}`;
            productsList.appendChild(li);
        });
    } catch (error) {
        console.error('Error fetching products:', error);
        productsList.innerHTML = `<li>Error fetching products: ${error.message}</li>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchUsers();
    fetchProducts();
});