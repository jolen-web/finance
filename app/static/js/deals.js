/**
 * Deals Widget - Professional credit card deals showcase
 * Modern, accessible, and responsive design
 */

class DealsWidget {
    constructor(containerSelector = '#deals-widget') {
        this.container = document.querySelector(containerSelector);
        this.deals = [];
        this.filteredDeals = [];
        this.currentPage = 0;
        this.pageSize = 12;
        this.viewMode = 'list'; // 'grid' or 'list'
        this.isLoading = false;
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

        // Design system tokens
        this.colors = {
            primary: '#2563eb',      // Blue
            secondary: '#1f2937',    // Dark gray
            accent: '#dc2626',       // Red for discounts
            success: '#10b981',      // Green
            warning: '#f59e0b',      // Amber
            border: '#e5e7eb',       // Light gray
            bg: '#f9fafb',           // Very light gray
            text: '#111827',         // Dark text
            textMuted: '#4b5563',    // Muted text (darker for WCAG AA contrast)
        };

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
        this.isLoading = true;
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
        } finally {
            this.isLoading = false;
        }
    }

    applyClientSideFilters() {
        let filtered = this.deals;

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

    toggleViewMode() {
        this.viewMode = this.viewMode === 'grid' ? 'list' : 'grid';
        this.currentPage = 0;
        this.render();
        this.attachEventListeners();
    }

    render() {
        this.container.innerHTML = '';

        const header = this.createHeader();
        this.container.appendChild(header);

        const grid = this.createDealsGrid();
        this.container.appendChild(grid);

        const pagination = this.createPagination();
        this.container.appendChild(pagination);
    }

    createHeader() {
        const header = document.createElement('div');
        header.className = 'deals-header';
        header.style.cssText = `
            background: white;
            border-bottom: 2px solid ${this.colors.border};
            padding: 1.5rem 0;
            margin-bottom: 2rem;
        `;

        const headerContent = document.createElement('div');
        headerContent.style.cssText = `
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 1.5rem;
        `;

        // Title section
        const titleSection = document.createElement('div');
        titleSection.style.cssText = `
            margin-bottom: 1.5rem;
        `;
        titleSection.innerHTML = `
            <h1 style="
                margin: 0 0 0.5rem 0;
                font-size: 1.875rem;
                font-weight: 700;
                color: ${this.colors.text};
                letter-spacing: -0.02em;
            ">💳 Exclusive Card Deals</h1>
            <p style="
                margin: 0;
                font-size: 1rem;
                color: ${this.colors.textMuted};
                font-weight: 400;
            ">Discover premium offers and rewards tailored for your credit cards</p>
        `;

        // Controls section
        const controlsSection = document.createElement('div');
        controlsSection.style.cssText = `
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 1rem;
            align-items: flex-end;
        `;

        // Search bar
        const searchContainer = document.createElement('div');
        searchContainer.style.cssText = `
            display: flex;
            align-items: center;
            background: ${this.colors.bg};
            border: 1px solid ${this.colors.border};
            border-radius: 8px;
            padding: 0.75rem 1rem;
            transition: all 0.2s ease;
        `;
        searchContainer.innerHTML = `
            <svg style="width: 18px; height: 18px; color: ${this.colors.textMuted}; margin-right: 0.5rem;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
            </svg>
            <input type="text" id="deals-search" placeholder="Search deals, merchants, or cards..."
                aria-label="Search deals by title, merchant, or card"
                style="
                    flex: 1;
                    border: none;
                    background: transparent;
                    font-size: 0.95rem;
                    color: ${this.colors.text};
                    outline: none;
                "
            >
        `;

        // Filters group
        const filtersGroup = document.createElement('div');
        filtersGroup.style.cssText = `
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
        `;

        const categorySelect = this.createSelectInput('deals-category-filter', 'Category', this.categories);
        const issuerSelect = this.createSelectInput('deals-issuer-filter', 'Issuer', this.issuers);
        const sortSelect = this.createSortSelect();
        const viewToggle = this.createViewToggle();

        filtersGroup.appendChild(categorySelect);
        filtersGroup.appendChild(issuerSelect);
        filtersGroup.appendChild(sortSelect);
        filtersGroup.appendChild(viewToggle);

        controlsSection.appendChild(searchContainer);
        controlsSection.appendChild(filtersGroup);

        headerContent.appendChild(titleSection);
        headerContent.appendChild(controlsSection);
        header.appendChild(headerContent);

        return header;
    }

    createSelectInput(id, label, options) {
        const wrapper = document.createElement('div');
        wrapper.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        `;

        const labelEl = document.createElement('label');
        labelEl.htmlFor = id;
        labelEl.style.cssText = `
            font-size: 0.75rem;
            font-weight: 600;
            color: ${this.colors.textMuted};
            text-transform: uppercase;
            letter-spacing: 0.05em;
        `;
        labelEl.textContent = label;

        const select = document.createElement('select');
        select.id = id;
        select.setAttribute('aria-label', `Filter deals by ${label}`);
        select.style.cssText = `
            padding: 0.65rem 0.875rem;
            border: 1px solid ${this.colors.border};
            border-radius: 6px;
            background: white;
            color: ${this.colors.text};
            font-size: 0.9375rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            min-width: 140px;
        `;

        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = `All ${label}s`;
        select.appendChild(defaultOption);

        options.forEach(opt => {
            const option = document.createElement('option');
            option.value = opt;
            option.textContent = opt;
            select.appendChild(option);
        });

        select.addEventListener('hover', () => {
            select.style.borderColor = this.colors.primary;
        });

        wrapper.appendChild(labelEl);
        wrapper.appendChild(select);
        return wrapper;
    }

    createSortSelect() {
        const wrapper = document.createElement('div');
        wrapper.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        `;

        const labelEl = document.createElement('label');
        labelEl.htmlFor = 'deals-sort-filter';
        labelEl.style.cssText = `
            font-size: 0.75rem;
            font-weight: 600;
            color: ${this.colors.textMuted};
            text-transform: uppercase;
            letter-spacing: 0.05em;
        `;
        labelEl.textContent = 'Sort By';

        const select = document.createElement('select');
        select.id = 'deals-sort-filter';
        select.setAttribute('aria-label', 'Sort deals by criteria');
        select.style.cssText = `
            padding: 0.65rem 0.875rem;
            border: 1px solid ${this.colors.border};
            border-radius: 6px;
            background: white;
            color: ${this.colors.text};
            font-size: 0.9375rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            min-width: 140px;
        `;

        const options = [
            { value: 'date', label: 'Newest First' },
            { value: 'discount', label: 'Highest Discount' },
            { value: 'quality', label: 'Best Quality' }
        ];

        options.forEach(opt => {
            const option = document.createElement('option');
            option.value = opt.value;
            option.textContent = opt.label;
            select.appendChild(option);
        });

        wrapper.appendChild(labelEl);
        wrapper.appendChild(select);
        return wrapper;
    }

    createViewToggle() {
        const wrapper = document.createElement('div');
        wrapper.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        `;

        const labelEl = document.createElement('label');
        labelEl.style.cssText = `
            font-size: 0.75rem;
            font-weight: 600;
            color: ${this.colors.textMuted};
            text-transform: uppercase;
            letter-spacing: 0.05em;
        `;
        labelEl.textContent = 'View';

        const toggleGroup = document.createElement('div');
        toggleGroup.style.cssText = `
            display: flex;
            gap: 0.375rem;
            background: ${this.colors.bg};
            padding: 0.375rem;
            border-radius: 6px;
            border: 1px solid ${this.colors.border};
        `;

        const gridBtn = document.createElement('button');
        gridBtn.id = 'view-grid';
        gridBtn.style.cssText = `
            padding: 0.5rem 0.75rem;
            background: ${this.viewMode === 'grid' ? this.colors.primary : 'transparent'};
            color: ${this.viewMode === 'grid' ? 'white' : this.colors.textMuted};
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.8125rem;
            transition: all 0.2s ease;
        `;
        gridBtn.innerHTML = '⊞ Grid';

        const listBtn = document.createElement('button');
        listBtn.id = 'view-list';
        listBtn.style.cssText = `
            padding: 0.5rem 0.75rem;
            background: ${this.viewMode === 'list' ? this.colors.primary : 'transparent'};
            color: ${this.viewMode === 'list' ? 'white' : this.colors.textMuted};
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.8125rem;
            transition: all 0.2s ease;
        `;
        listBtn.innerHTML = '☰ List';

        toggleGroup.appendChild(gridBtn);
        toggleGroup.appendChild(listBtn);

        wrapper.appendChild(labelEl);
        wrapper.appendChild(toggleGroup);
        return wrapper;
    }

    createDealsGrid() {
        const grid = document.createElement('div');
        grid.className = 'deals-grid';
        grid.setAttribute('aria-live', 'polite');
        grid.setAttribute('aria-label', `${this.filteredDeals.length} credit card deals available`);
        grid.style.cssText = `
            ${this.viewMode === 'grid'
                ? 'display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.5rem;'
                : 'display: flex; flex-direction: column; gap: 1rem;'
            }
            margin-bottom: 3rem;
            max-width: 1400px;
            margin-left: auto;
            margin-right: auto;
            padding: 0 1.5rem;
        `;

        if (this.filteredDeals.length === 0) {
            grid.innerHTML = `
                <div style="
                    grid-column: 1/-1;
                    text-align: center;
                    padding: 3rem 1rem;
                    background: ${this.colors.bg};
                    border-radius: 12px;
                    border: 2px dashed ${this.colors.border};
                ">
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">🔍</div>
                    <h3 style="
                        margin: 0 0 0.5rem 0;
                        font-size: 1.1rem;
                        color: ${this.colors.text};
                        font-weight: 600;
                    ">No deals found</h3>
                    <p style="
                        margin: 0;
                        color: ${this.colors.textMuted};
                        font-size: 0.9375rem;
                    ">Try adjusting your filters or search terms</p>
                </div>
            `;
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

        // Square card layout for grid view
        if (this.viewMode === 'grid') {
            card.style.cssText = `
                background: white;
                border: 1px solid ${this.colors.border};
                border-radius: 12px;
                overflow: hidden;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
                aspect-ratio: 1;
                display: flex;
                flex-direction: column;
                position: relative;
            `;

            card.addEventListener('mouseenter', () => {
                card.style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.12)';
                card.style.transform = 'translateY(-4px)';
            });

            card.addEventListener('mouseleave', () => {
                card.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.08)';
                card.style.transform = 'translateY(0)';
            });

            // Image takes up full square, or show gradient background if no image
            const imgWrapper = document.createElement('div');
            imgWrapper.style.cssText = `
                position: absolute;
                width: 100%;
                height: 100%;
                overflow: hidden;
                background: linear-gradient(135deg, ${this.colors.primary} 0%, ${this.colors.secondary} 100%);
                display: flex;
                align-items: center;
                justify-content: center;
            `;

            if (deal.image_url) {
                imgWrapper.innerHTML = `
                    <img src="${deal.image_url}"
                         alt="${deal.title} - ${deal.category} deal from ${deal.card_issuer}"
                         style="width: 100%; height: 100%; object-fit: cover;"
                         decoding="async">
                `;
            }
            card.appendChild(imgWrapper);

            // Overlay gradient at bottom for readability
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                height: 100%;
                background: linear-gradient(to top, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.4) 50%, transparent 100%);
                pointer-events: none;
            `;
            card.appendChild(overlay);

            // Discount badge overlay (top right, blue circle)
            const badge = document.createElement('div');
            badge.style.cssText = `
                position: absolute;
                top: 0.75rem;
                right: 0.75rem;
                width: 56px;
                height: 56px;
                background: ${this.colors.primary};
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 700;
                font-size: 1.125rem;
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
                text-align: center;
                flex-direction: column;
                z-index: 10;
            `;

            if (deal.discount_percent) {
                badge.innerHTML = `<span style="font-size: 1.375rem; line-height: 1;">${deal.discount_percent}%</span>`;
            } else if (deal.discount_type === 'BOGO') {
                badge.innerHTML = `<span style="font-size: 0.75rem; line-height: 1.2;">BOGO</span>`;
            } else if (deal.cashback_percent) {
                badge.innerHTML = `<span style="font-size: 1.375rem; line-height: 1;">${deal.cashback_percent}%</span>`;
            } else {
                badge.innerHTML = `<span style="font-size: 1.5rem;">✨</span>`;
            }
            card.appendChild(badge);

            // Content at bottom (title, merchant, category, discount)
            const cardContent = document.createElement('div');
            cardContent.style.cssText = `
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                padding: 1rem;
                z-index: 5;
                color: white;
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            `;

            // Build discount label
            let discountLabel = deal.card_issuer || 'Exclusive';
            if (deal.discount_percent) {
                discountLabel = `${deal.discount_percent}% OFF`;
            } else if (deal.discount_type === 'bogo') {
                discountLabel = 'BOGO';
            } else if (deal.cashback_percent) {
                discountLabel = `${deal.cashback_percent}% CB`;
            } else if (deal.reward_points) {
                discountLabel = 'Earn Points';
            }

            // Determine badge color based on card issuer
            let badgeColor = 'rgba(37, 99, 235, 0.8)'; // Default blue
            if (deal.card_issuer === 'BPI') {
                badgeColor = 'rgba(220, 38, 38, 0.8)'; // Red for BPI
            } else if (deal.card_issuer === 'BDO') {
                badgeColor = 'rgba(37, 99, 235, 0.8)'; // Blue for BDO
            }

            // Show consistent content across all cards: title, merchant, category, discount
            const contentHTML = `
                <h3 style="
                    margin: 0 0 0.25rem 0;
                    font-size: 0.95rem;
                    font-weight: 700;
                    color: white;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    line-height: 1.2;
                ">${deal.title}</h3>
                <p style="
                    margin: 0 0 0.5rem 0;
                    font-size: 0.75rem;
                    color: rgba(255,255,255,0.85);
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    font-weight: 500;
                ">${deal.merchant || 'Various'}</p>
                <div style="
                    display: flex;
                    gap: 0.5rem;
                    flex-wrap: wrap;
                    align-items: center;
                ">
                    <span style="
                        background: rgba(255,255,255,0.25);
                        border-radius: 4px;
                        padding: 0.25rem 0.5rem;
                        font-size: 0.65rem;
                        font-weight: 600;
                        color: white;
                        text-transform: uppercase;
                        white-space: nowrap;
                    ">${deal.category || 'General'}</span>
                    <span style="
                        background: ${badgeColor};
                        border-radius: 4px;
                        padding: 0.25rem 0.5rem;
                        font-size: 0.65rem;
                        font-weight: 700;
                        color: white;
                        white-space: nowrap;
                    ">${discountLabel}</span>
                </div>
            `;

            cardContent.innerHTML = contentHTML;
            card.appendChild(cardContent);

        } else {
            // List view: horizontal layout - compact without images
            card.style.cssText = `
                background: white;
                border: 1px solid ${this.colors.border};
                border-radius: 8px;
                overflow: hidden;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
                display: flex;
                flex-direction: row;
                max-width: 100%;
                align-items: center;
                padding: 0.75rem 1rem;
            `;

            card.addEventListener('mouseenter', () => {
                card.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
                card.style.transform = 'translateY(-1px)';
            });

            card.addEventListener('mouseleave', () => {
                card.style.boxShadow = '0 1px 2px rgba(0, 0, 0, 0.05)';
                card.style.transform = 'translateY(0)';
            });

            const cardContent = document.createElement('div');
            cardContent.style.cssText = `flex: 1; display: flex; flex-direction: column; gap: 0.25rem;`;

            // Build discount label for list view
            let discountLabel = deal.card_issuer || 'Exclusive';
            if (deal.discount_percent) {
                discountLabel = `${deal.discount_percent}% OFF`;
            } else if (deal.discount_type === 'bogo') {
                discountLabel = 'BOGO';
            } else if (deal.cashback_percent) {
                discountLabel = `${deal.cashback_percent}% CB`;
            } else if (deal.reward_points) {
                discountLabel = 'Earn Points';
            }

            // Determine badge color based on card issuer
            let badgeColor = this.colors.primary; // Default blue
            if (deal.card_issuer === 'BPI') {
                badgeColor = this.colors.accent; // Red for BPI
            } else if (deal.card_issuer === 'BDO') {
                badgeColor = this.colors.primary; // Blue for BDO
            }

            cardContent.innerHTML = `
                <h3 style="
                    margin: 0;
                    font-size: 0.9rem;
                    font-weight: 700;
                    color: ${this.colors.text};
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    line-height: 1.2;
                ">${deal.title}</h3>
                <div style="
                    display: flex;
                    gap: 0.5rem;
                    flex-wrap: wrap;
                    align-items: center;
                ">
                    <span style="
                        background: ${this.colors.bg};
                        border: 1px solid ${this.colors.border};
                        border-radius: 3px;
                        padding: 0.2rem 0.4rem;
                        font-size: 0.6rem;
                        font-weight: 600;
                        color: ${this.colors.text};
                        text-transform: uppercase;
                        white-space: nowrap;
                    ">${deal.category || 'General'}</span>
                    <span style="
                        background: ${badgeColor};
                        border-radius: 3px;
                        padding: 0.2rem 0.4rem;
                        font-size: 0.6rem;
                        font-weight: 700;
                        color: white;
                        white-space: nowrap;
                    ">${discountLabel}</span>
                </div>
            `;
            card.appendChild(cardContent);
        }

        card.addEventListener('click', () => this.showDealModal(deal));

        return card;
    }

    createDiscountBadge(deal) {
        const badge = document.createElement('div');
        badge.style.cssText = `
            background: ${this.colors.accent};
            color: white;
            padding: 0.625rem 0.875rem;
            border-radius: 8px;
            text-align: center;
            min-width: 65px;
            white-space: nowrap;
            font-weight: 700;
            box-shadow: 0 2px 8px rgba(220, 38, 38, 0.25);
        `;

        if (deal.discount_percent) {
            badge.innerHTML = `
                <div style="font-size: 1.25rem; line-height: 1;">${deal.discount_percent}%</div>
                <div style="font-size: 0.625rem; line-height: 1; margin-top: 0.1rem;">OFF</div>
            `;
        } else if (deal.discount_type === 'BOGO') {
            badge.innerHTML = `<div style="font-size: 0.875rem;">BOGO</div>`;
        } else if (deal.cashback_percent) {
            badge.innerHTML = `
                <div style="font-size: 1.25rem; line-height: 1;">${deal.cashback_percent}%</div>
                <div style="font-size: 0.625rem; line-height: 1; margin-top: 0.1rem;">CB</div>
            `;
        } else {
            badge.innerHTML = `<div style="font-size: 0.875rem;">✨</div>`;
        }

        return badge;
    }

    createPagination() {
        const wrapper = document.createElement('div');
        wrapper.style.cssText = `
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.75rem;
            flex-wrap: wrap;
            padding: 1rem 0;
            max-width: 1400px;
            margin: 0 auto;
        `;

        const totalPages = Math.ceil(this.filteredDeals.length / this.pageSize);

        if (totalPages <= 1) return wrapper;

        // Previous button
        const prevBtn = document.createElement('button');
        prevBtn.textContent = '← Previous';
        prevBtn.style.cssText = `
            padding: 0.625rem 1rem;
            border: 1px solid ${this.colors.border};
            border-radius: 6px;
            background: white;
            color: ${this.colors.text};
            cursor: ${this.currentPage === 0 ? 'not-allowed' : 'pointer'};
            opacity: ${this.currentPage === 0 ? '0.5' : '1'};
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 0.2s ease;
        `;
        if (this.currentPage > 0) {
            prevBtn.addEventListener('click', () => {
                this.currentPage--;
                this.render();
                this.attachEventListeners();
                this.container.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        }
        wrapper.appendChild(prevBtn);

        // Page numbers
        const pageStart = Math.max(0, this.currentPage - 2);
        const pageEnd = Math.min(totalPages, this.currentPage + 3);

        if (pageStart > 0) {
            const firstPage = document.createElement('button');
            firstPage.textContent = '1';
            firstPage.style.cssText = `
                padding: 0.5rem 0.75rem;
                border: 1px solid ${this.colors.border};
                border-radius: 6px;
                background: white;
                color: ${this.colors.text};
                cursor: pointer;
                font-weight: 500;
            `;
            firstPage.addEventListener('click', () => {
                this.currentPage = 0;
                this.render();
                this.attachEventListeners();
                this.container.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
            wrapper.appendChild(firstPage);

            if (pageStart > 1) {
                const dots = document.createElement('span');
                dots.textContent = '...';
                dots.style.cssText = `color: ${this.colors.textMuted}; padding: 0.5rem 0.25rem;`;
                wrapper.appendChild(dots);
            }
        }

        for (let i = pageStart; i < pageEnd; i++) {
            const button = document.createElement('button');
            button.textContent = i + 1;
            button.style.cssText = `
                padding: 0.5rem 0.75rem;
                border: 1px solid ${i === this.currentPage ? this.colors.primary : this.colors.border};
                border-radius: 6px;
                background: ${i === this.currentPage ? this.colors.primary : 'white'};
                color: ${i === this.currentPage ? 'white' : this.colors.text};
                cursor: pointer;
                font-weight: ${i === this.currentPage ? '700' : '500'};
                transition: all 0.2s ease;
            `;

            button.addEventListener('click', () => {
                this.currentPage = i;
                this.render();
                this.attachEventListeners();
                this.container.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });

            wrapper.appendChild(button);
        }

        // Ellipsis and last page
        if (pageEnd < totalPages) {
            if (pageEnd < totalPages - 1) {
                const dots = document.createElement('span');
                dots.textContent = '...';
                dots.style.cssText = `color: ${this.colors.textMuted}; padding: 0.5rem 0.25rem;`;
                wrapper.appendChild(dots);
            }

            const lastPage = document.createElement('button');
            lastPage.textContent = totalPages;
            lastPage.style.cssText = `
                padding: 0.5rem 0.75rem;
                border: 1px solid ${this.colors.border};
                border-radius: 6px;
                background: white;
                color: ${this.colors.text};
                cursor: pointer;
                font-weight: 500;
            `;
            lastPage.addEventListener('click', () => {
                this.currentPage = totalPages - 1;
                this.render();
                this.attachEventListeners();
                this.container.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
            wrapper.appendChild(lastPage);
        }

        // Next button
        const nextBtn = document.createElement('button');
        nextBtn.textContent = 'Next →';
        nextBtn.style.cssText = `
            padding: 0.625rem 1rem;
            border: 1px solid ${this.colors.border};
            border-radius: 6px;
            background: white;
            color: ${this.colors.text};
            cursor: ${this.currentPage === totalPages - 1 ? 'not-allowed' : 'pointer'};
            opacity: ${this.currentPage === totalPages - 1 ? '0.5' : '1'};
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 0.2s ease;
        `;
        if (this.currentPage < totalPages - 1) {
            nextBtn.addEventListener('click', () => {
                this.currentPage++;
                this.render();
                this.attachEventListeners();
                this.container.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        }
        wrapper.appendChild(nextBtn);

        return wrapper;
    }

    showDealModal(deal) {
        const modal = document.createElement('div');
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-label', `${deal.title} deal details`);
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
            padding: 1rem;
            animation: fadeIn 0.2s ease-out;
        `;

        // Store previous focus for restoration
        this.previousFocus = document.activeElement;

        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            border-radius: 16px;
            padding: 2rem;
            max-width: 600px;
            width: 100%;
            max-height: 85vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        `;

        content.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1.5rem;">
                <h2 style="
                    margin: 0;
                    color: ${this.colors.text};
                    font-size: 1.5rem;
                    font-weight: 700;
                    flex: 1;
                ">${deal.title}</h2>
                <button aria-label="Close deal details" style="
                    background: ${this.colors.bg};
                    border: none;
                    border-radius: 8px;
                    font-size: 1.5rem;
                    width: 40px;
                    height: 40px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s ease;
                ">×</button>
            </div>

            ${deal.image_url ? `
                <div style="
                    margin-bottom: 1.5rem;
                    border-radius: 12px;
                    overflow: hidden;
                    max-height: 300px;
                ">
                    <img src="${deal.image_url}" alt="${deal.title}"
                         style="width: 100%; height: 100%; object-fit: cover; display: block;">
                </div>
            ` : ''}

            <div style="
                background: linear-gradient(135deg, ${this.colors.primary} 0%, ${this.colors.secondary} 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 12px;
                margin-bottom: 1.5rem;
                text-align: center;
            ">
                ${deal.discount_percent ? `<div style="font-size: 2.5rem; font-weight: 700; line-height: 1;">${deal.discount_percent}% OFF</div>` : ''}
                ${deal.discount_type === 'BOGO' ? `<div style="font-size: 1.5rem; font-weight: 700;">Buy One, Get One</div>` : ''}
                ${deal.cashback_percent ? `<div style="font-size: 2.5rem; font-weight: 700; line-height: 1;">${deal.cashback_percent}% Cashback</div>` : ''}
                ${deal.reward_points ? `<div style="font-size: 2.5rem; font-weight: 700; line-height: 1;">${deal.reward_points} Points</div>` : ''}
            </div>

            <div style="margin-bottom: 1.5rem;">
                <h3 style="
                    color: ${this.colors.text};
                    margin-bottom: 0.5rem;
                    font-size: 1.125rem;
                    font-weight: 700;
                ">About This Offer</h3>
                <p style="
                    color: ${this.colors.textMuted};
                    line-height: 1.6;
                    margin: 0;
                    font-size: 0.95rem;
                ">${deal.description || deal.detailed_description || 'Exclusive credit card offer'}</p>
            </div>

            <div style="
                background: ${this.colors.bg};
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1.5rem;
            ">
                <div style="
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 1rem;
                ">
                    <div>
                        <div style="
                            font-size: 0.75rem;
                            font-weight: 600;
                            color: ${this.colors.textMuted};
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                            margin-bottom: 0.25rem;
                        ">Card Issuer</div>
                        <div style="
                            font-size: 0.95rem;
                            font-weight: 700;
                            color: ${this.colors.text};
                        ">${deal.card_issuer}</div>
                    </div>
                    <div>
                        <div style="
                            font-size: 0.75rem;
                            font-weight: 600;
                            color: ${this.colors.textMuted};
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                            margin-bottom: 0.25rem;
                        ">Category</div>
                        <div style="
                            font-size: 0.95rem;
                            font-weight: 700;
                            color: ${this.colors.text};
                        ">${deal.category || 'General'}</div>
                    </div>
                    <div>
                        <div style="
                            font-size: 0.75rem;
                            font-weight: 600;
                            color: ${this.colors.textMuted};
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                            margin-bottom: 0.25rem;
                        ">Merchant</div>
                        <div style="
                            font-size: 0.95rem;
                            font-weight: 700;
                            color: ${this.colors.text};
                        ">${deal.merchant || 'Various'}</div>
                    </div>
                </div>
            </div>

            ${deal.url ? `
                <a href="${deal.url}" target="_blank" style="
                    display: block;
                    background: ${this.colors.primary};
                    color: white;
                    padding: 1rem;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 700;
                    text-align: center;
                    transition: all 0.2s ease;
                ">
                    View Full Details on BDO Website →
                </a>
            ` : ''}
        `;

        // Add animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        document.head.appendChild(style);

        modal.appendChild(content);

        // Close modal handlers
        const closeHandler = () => {
            modal.remove();
            // Restore focus to previous element
            if (this.previousFocus) {
                this.previousFocus.focus();
            }
        };

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeHandler();
        });

        // Close on Escape key
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeHandler();
        });

        // Close on close button click
        const closeBtn = content.querySelector('button[aria-label*="Close"]');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeHandler);
        }

        document.body.appendChild(modal);

        // Move focus to modal heading
        const heading = modal.querySelector('h2');
        if (heading) {
            heading.setAttribute('tabindex', '-1');
            heading.focus();
        }
    }

    attachEventListeners() {
        // Use event delegation to avoid duplicate listeners
        // Only attach to container once with a flag
        if (this.container._listenersAttached) {
            this.updateFilterUI();
            return;
        }
        this.container._listenersAttached = true;

        // Attach single delegated listeners to container
        this.container.addEventListener('input', (e) => {
            if (e.target.id === 'deals-search') {
                this.filters.searchTerm = e.target.value;
                this.currentPage = 0;
                this.applyClientSideFilters();
                this.render();
            }
        });

        this.container.addEventListener('change', async (e) => {
            if (e.target.id === 'deals-category-filter') {
                this.filters.category = e.target.value || null;
                this.currentPage = 0;
                await this.loadDeals();
                this.render();
            } else if (e.target.id === 'deals-issuer-filter') {
                this.filters.issuer = e.target.value || null;
                this.currentPage = 0;
                await this.loadDeals();
                this.render();
            } else if (e.target.id === 'deals-sort-filter') {
                this.filters.sortBy = e.target.value;
                this.currentPage = 0;
                await this.loadDeals();
                this.render();
            }
        });

        this.container.addEventListener('click', (e) => {
            if (e.target.id === 'view-grid') {
                if (this.viewMode !== 'grid') {
                    this.viewMode = 'grid';
                    this.currentPage = 0;
                    this.render();
                }
            } else if (e.target.id === 'view-list') {
                if (this.viewMode !== 'list') {
                    this.viewMode = 'list';
                    this.currentPage = 0;
                    this.render();
                }
            }
        });

        this.updateFilterUI();
    }

    updateFilterUI() {
        // Update dropdown selected values to reflect current filters
        const categoryFilter = document.getElementById('deals-category-filter');
        const issuerFilter = document.getElementById('deals-issuer-filter');
        const sortFilter = document.getElementById('deals-sort-filter');
        const searchInput = document.getElementById('deals-search');

        if (categoryFilter) {
            categoryFilter.value = this.filters.category || '';
        }
        if (issuerFilter) {
            issuerFilter.value = this.filters.issuer || '';
        }
        if (sortFilter) {
            sortFilter.value = this.filters.sortBy;
        }
        if (searchInput) {
            searchInput.value = this.filters.searchTerm || '';
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
