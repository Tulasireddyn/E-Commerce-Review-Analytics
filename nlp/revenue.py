def estimate_revenue(product_data):
    """
    Estimates monthly revenue based on heuristics.
    Since we don't have Amazon's internal BSR (Best Sellers Rank) data,
    we use a proxy formula based on review count and rating.
    """
    price = product_data.get('price', 0.0)
    review_count = product_data.get('review_count', 0)
    rating = product_data.get('rating', 0.0)
    
    # Naive heuristic: Assume a fraction of buyers leave reviews, 
    # and infer a monthly rate based on a very rough estimate.
    # In a real app, this would use BSR to Sales lookup tables.
    estimated_monthly_sales = int((rating * 10) + (review_count * 0.015))
    
    # Ensure some baseline
    if estimated_monthly_sales <= 0 and price > 0:
        estimated_monthly_sales = 25
        
    monthly_revenue = estimated_monthly_sales * price
    
    return {
        'estimated_monthly_sales': estimated_monthly_sales,
        'estimated_monthly_revenue': round(monthly_revenue, 2)
    }
