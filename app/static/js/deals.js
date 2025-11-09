/**
 * Deals Widget - Display credit card deals and promotions
 * Features: filtering, search, sorting, pagination
 */

class DealsWidget {
    constructor(containerSelector = '#deals-widget') {
        this.container = document.querySelector(containerSelector);
        this.deals = [];
        this.filteredDeals = [];
        this.currentPage = 0;
        this.pageSize = 12;
        this.filters = {
            category: null,
            merchant: null,
            issuer: null,
            minDiscount: null,
            searchTerm: null,
            sortBy: 'date'
        };
        this.categories = [];
        this.merchants = [];
        this.issuers = [];

        if (this.container) {
            this.init();
        }
    }

    async init() {
        console.log('Initializing Deals Widget');
        await this.loadFilterOptions();
        await this.loadDeals();
        this.render();
        this.attachEventListeners();
    }

    async loadFilterOptions() {
        try {
            const [catRes, merRes, issRes] = await Promise.all([
                fetch('/api/deals/categories'),
                fetch('/api/deals/merchants'),
                fetch('/api/deals/card-issuers')
            ]);

            const catData = await catRes.json();
            const merData = await merRes.json();
            const issData = await issRes.json();

            if (catData.success) this.categories = catData.data;
            if (merData.success) this.merchants = merData.data;
            if (issData.success) this.issuers = issData.data;

            console.log('Filter options loaded:', {
                categories: this.categories.length,
                merchants: this.merchants.length,
                issuers: this.issuers.length
            });
        } catch (error) {
            console.error('Error loading filter options:', error);
        }
    }

    async loadDeals(limit = 100) {
        try {
            const params = new URLSearchParams({
                limit: limit,
                offset: this.currentPage * this.pageSize,
                sort_by: this.filters.sortBy
            });

            if (this.filters.category) params.append('category', this.filters.category);
            if (this.filters.merchant) params.append('merchant', this.filters.merchant);
            if (this.filters.issuer) params.append('card_issuer', this.filters.issuer);
            if (this.filters.minDiscount) params.append('min_discount', this.filters.minDiscount);
            if (this.filters.searchTerm) params.append('search', this.filters.searchTerm);

            const response = await fetch(`/api/deals?${params}`);
            const data = await response.json();

            if (data.success) {
                this.deals = data.data;
                this.applyClientSideFilters();
                console.log(`Loaded ${this.deals.length} deals`);
            } else {
                console.error('Error loading deals:', data.error);
            }
        } catch (error) {
            console.error('Error fetching deals:', error);
        }
    }

    applyClientSideFilters() {
        let filtered = this.deals;

        // Client-side search filter (in addition to server-side)
        if (this.filters.searchTerm) {
            const term = this.filters.searchTerm.toLowerCase();
            filtered = filtered.filter(deal =>
                deal.title.toLowerCase().includes(term) ||
                deal.description.toLowerCase().includes(term) ||
                deal.merchant?.toLowerCase().includes(term)
            );
        }

        this.filteredDeals = filtered;
    }

    render() {
        this.container.innerHTML = '';

        // Create header with filters
        const header = this.createHeader();
        this.container.appendChild(header);

        // Create deals grid
        const grid = this.createDealsGrid();
        this.container.appendChild(grid);

        // Create pagination
        const pagination = this.createPagination();
        this.container.appendChild(pagination);
    }

    createHeader() {
        const header = document.createElement('div');
        header.className = 'deals-header';
        header.innerHTML = `
            <div class="deals-title">
                <h2>💳 Credit Card Deals</h2>
                <p>Find the best offers for your credit cards</p>
            </div>
            <div class="deals-controls">
                <div class="deals-search">
                    <input type="text" id="deals-search" placeholder="Search deals..." class="deals-search-input">
                </div>
                <div class="deals-filters">
                    <select id="deals-category-filter" class="deals-filter-select">
                        <option value="">All Categories</option>
                        ${this.categories.map(cat => `<option value="${cat}">${cat}</option>`).join('')}
                    </select>
                    <select id="deals-issuer-filter" class="deals-filter-select">
                        <option value="">All Issuers</option>
                        ${this.issuers.map(issuer => `<option value="${issuer}">${issuer}</option>`).join('')}
                    </select>
                    <select id="deals-sort-filter" class="deals-filter-select">
                        <option value="date">Newest First</option>
                        <option value="discount">Highest Discount</option>
                        <option value="quality">Best Quality</option>
                    </select>
                </div>
            </div>
        `;

        header.style.cssText = `
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        `;

        return header;
    }

    createDealsGrid() {
        const grid = document.createElement('div');
        grid.className = 'deals-grid';
        grid.style.cssText = `
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        `;

        if (this.filteredDeals.length === 0) {
            grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">No deals found. Try adjusting your filters.</p>';
            return grid;
        }

        const start = this.currentPage * this.pageSize;
        const end = start + this.pageSize;
        const pageDeals = this.filteredDeals.slice(start, end);

        pageDeals.forEach(deal => {
            const card = this.createDealCard(deal);
            grid.appendChild(card);
        });

        return grid;
    }

    createDealCard(deal) {
        const card = document.createElement('div');
        card.className = 'deal-card';
        card.style.cssText = `
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        `;

        card.addEventListener('mouseenter', () => {
            card.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.15)';
            card.style.transform = 'translateY(-4px)';
        });

        card.addEventListener('mouseleave', () => {
            card.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.05)';
            card.style.transform = 'translateY(0)';
        });

        const discountBadge = this.createDiscountBadge(deal);
        const header = document.createElement('div');
        header.style.cssText = 'display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;';

        const titleDiv = document.createElement('div');
        titleDiv.style.cssText = 'flex: 1;';
        titleDiv.innerHTML = `
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.1rem; color: #333;">${deal.title}</h3>
            <p style="margin: 0; font-size: 0.9rem; color: #666;">
                ${deal.merchant || 'General'}
            </p>
        `;

        header.appendChild(titleDiv);
        header.appendChild(discountBadge);

        const details = document.createElement('div');
        details.style.cssText = 'margin-bottom: 1rem;';
        details.innerHTML = `
            <p style="margin: 0.5rem 0; font-size: 0.95rem; color: #555; line-height: 1.4;">
                ${deal.description || 'Great deal on credit card'}
            </p>
            ${deal.category ? `<div style="margin-top: 0.5rem;"><span style="display: inline-block; background: #f0f0f0; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.85rem; color: #666;">${deal.category}</span></div>` : ''}
        `;

        const footer = document.createElement('div');
        footer.style.cssText = 'border-top: 1px solid #f0f0f0; padding-top: 1rem; font-size: 0.9rem; color: #999;';
        footer.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>${deal.card_issuer}</span>
                ${deal.promotion?.end_date ? `<span>Until ${deal.promotion.end_date}</span>` : '<span>Active</span>'}
            </div>
        `;

        card.appendChild(header);
        card.appendChild(details);
        card.appendChild(footer);

        card.addEventListener('click', () => this.showDealModal(deal));

        return card;
    }

    createDiscountBadge(deal) {
        const badge = document.createElement('div');
        badge.style.cssText = `
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            text-align: center;
            min-width: 70px;
            margin-left: 1rem;
        `;

        if (deal.discount.percent) {
            badge.innerHTML = `<div style="font-size: 1.4rem; font-weight: bold;">${deal.discount.percent}%</div><div style="font-size: 0.75rem;">OFF</div>`;
        } else if (deal.discount.type === 'BOGO') {
            badge.innerHTML = `<div style="font-size: 0.9rem; font-weight: bold;">BOGO</div>`;
        } else if (deal.discount.cashback) {
            badge.innerHTML = `<div style="font-size: 1.4rem; font-weight: bold;">${deal.discount.cashback}%</div><div style="font-size: 0.75rem;">CB</div>`;
        } else {
            badge.innerHTML = `<div style="font-size: 0.9rem; font-weight: bold;">✨ Deal</div>`;
        }

        return badge;
    }

    createPagination() {
        const pagination = document.createElement('div');
        pagination.className = 'deals-pagination';
        pagination.style.cssText = `
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        `;

        const totalPages = Math.ceil(this.filteredDeals.length / this.pageSize);

        for (let i = 0; i < totalPages; i++) {
            const button = document.createElement('button');
            button.textContent = i + 1;
            button.className = i === this.currentPage ? 'active' : '';
            button.style.cssText = `
                padding: 0.5rem 1rem;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: ${i === this.currentPage ? '#667eea' : 'white'};
                color: ${i === this.currentPage ? 'white' : '#666'};
                cursor: pointer;
                transition: all 0.2s ease;
            `;

            button.addEventListener('click', () => {
                this.currentPage = i;
                this.render();
                this.attachEventListeners();
                this.container.scrollIntoView({ behavior: 'smooth' });
            });

            pagination.appendChild(button);
        }

        return pagination;
    }

    showDealModal(deal) {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        `;

        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 2rem;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        `;

        content.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1.5rem;">
                <h2 style="margin: 0; color: #333;">${deal.title}</h2>
                <button onclick="this.closest('[style*=position]').remove()" style="background: none; border: none; font-size: 1.5rem; cursor: pointer;">×</button>
            </div>

            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; text-align: center;">
                ${deal.discount.percent ? `<div style="font-size: 3rem; font-weight: bold;">${deal.discount.percent}% OFF</div>` : ''}
                ${deal.discount.type === 'BOGO' ? `<div style="font-size: 2rem; font-weight: bold;">Buy One, Get One</div>` : ''}
                ${deal.discount.cashback ? `<div style="font-size: 2rem; font-weight: bold;">${deal.discount.cashback}% Cashback</div>` : ''}
            </div>

            <div style="margin-bottom: 1.5rem;">
                <h3 style="color: #333; margin-bottom: 0.5rem;">Description</h3>
                <p style="color: #666; line-height: 1.6;">${deal.description}</p>
            </div>

            ${deal.promotion?.details ? `
                <div style="margin-bottom: 1.5rem;">
                    <h3 style="color: #333; margin-bottom: 0.5rem;">Details</h3>
                    <p style="color: #666;">${deal.promotion.details}</p>
                </div>
            ` : ''}

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
                <div>
                    <h4 style="color: #999; font-size: 0.9rem; margin: 0 0 0.5rem 0;">Card Issuer</h4>
                    <p style="color: #333; margin: 0; font-weight: 500;">${deal.card_issuer}</p>
                </div>
                <div>
                    <h4 style="color: #999; font-size: 0.9rem; margin: 0 0 0.5rem 0;">Category</h4>
                    <p style="color: #333; margin: 0; font-weight: 500;">${deal.category || 'General'}</p>
                </div>
                <div>
                    <h4 style="color: #999; font-size: 0.9rem; margin: 0 0 0.5rem 0;">Merchant</h4>
                    <p style="color: #333; margin: 0; font-weight: 500;">${deal.merchant || 'Various'}</p>
                </div>
                <div>
                    <h4 style="color: #999; font-size: 0.9rem; margin: 0 0 0.5rem 0;">Valid Until</h4>
                    <p style="color: #333; margin: 0; font-weight: 500;">${deal.promotion?.end_date || 'Ongoing'}</p>
                </div>
            </div>

            ${deal.url ? `
                <div style="text-align: center;">
                    <a href="${deal.url}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.75rem 2rem; border-radius: 8px; text-decoration: none; font-weight: 500; transition: transform 0.2s ease;">
                        View Details →
                    </a>
                </div>
            ` : ''}
        `;

        modal.appendChild(content);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });

        document.body.appendChild(modal);
    }

    attachEventListeners() {
        const searchInput = document.getElementById('deals-search');
        const categoryFilter = document.getElementById('deals-category-filter');
        const issuerFilter = document.getElementById('deals-issuer-filter');
        const sortFilter = document.getElementById('deals-sort-filter');

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filters.searchTerm = e.target.value;
                this.currentPage = 0;
                this.applyClientSideFilters();
                this.render();
                this.attachEventListeners();
            });
        }

        if (categoryFilter) {
            categoryFilter.addEventListener('change', (e) => {
                this.filters.category = e.target.value || null;
                this.currentPage = 0;
                this.loadDeals();
            });
        }

        if (issuerFilter) {
            issuerFilter.addEventListener('change', (e) => {
                this.filters.issuer = e.target.value || null;
                this.currentPage = 0;
                this.loadDeals();
            });
        }

        if (sortFilter) {
            sortFilter.addEventListener('change', (e) => {
                this.filters.sortBy = e.target.value;
                this.currentPage = 0;
                this.loadDeals();
            });
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new DealsWidget('#deals-widget');
    });
} else {
    new DealsWidget('#deals-widget');
}
