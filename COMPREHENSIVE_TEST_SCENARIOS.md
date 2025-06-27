# 🧪 Comprehensive Test Scenarios for BIST Portfolio Tracker

This document provides detailed test scenarios to thoroughly test all features of the portfolio tracking application with realistic data and edge cases.

## 📅 **Scenario 1: New Portfolio Build-Up (January 2025)**

### **Week 1: Initial Cash Deposits & First Purchases**
```
Jan 2, 2025: Cash Deposit - 100,000 TL
Jan 3, 2025: TUPRS hissesinden 200 adet hisse 285.50 TL fiyattan alinmistir.
Jan 5, 2025: THYAO hissesinden 300 adet hisse 98.75 TL fiyattan alinmistir.
Jan 8, 2025: SISE senedinden 150 adet 46.20 TL fiyat ile alim islemi gerceklestirilmistir.
```

### **Week 2: Adding More Positions**
```
Jan 10, 2025: CCOLA hissesinden 500 adet hisse 82.40 TL fiyattan alinmistir.
Jan 12, 2025: BIMAS senedinden 75 adet 248.90 TL fiyat ile alim islemi gerceklestirilmistir.
Jan 15, 2025: KRVGD hissesinden 1000 adet hisse 13.25 TL fiyattan alinmistir.
```

### **Week 3: First Dividend Received**
```
Jan 18, 2025: Degerli Musterimiz, THYAO.E senedi %45.20 temettu vermis, hesaplariniza yansitilmistir.
Jan 20, 2025: AEFES hissesinden 200 adet hisse 124.60 TL fiyattan alinmistir.
```

## 📊 **Scenario 2: Active Trading Period (February 2025)**

### **Portfolio Rebalancing**
```
Feb 1, 2025: TUPRS hissesinden 100 adet hisse 295.80 TL fiyattan satilmistir.
Feb 3, 2025: THYAO hissesinden 150 adet hisse 102.30 TL fiyattan satilmistir.
Feb 5, 2025: ISDMR senedinden 400 adet 35.75 TL fiyat ile alim islemi gerceklestirilmistir.
Feb 8, 2025: TOASO hissesinden 80 adet hisse 167.40 TL fiyattan alinmistir.
```

### **Mixed Transactions**
```
Feb 10, 2025: SISE senedinden 50 adet 48.90 TL fiyat ile satis islemi gerceklestirilmistir.
Feb 12, 2025: Cash Deposit - 25,000 TL
Feb 15, 2025: AGHOL hissesinden 120 adet hisse 89.20 TL fiyattan alinmistir.
Feb 18, 2025: CCOLA hissesinden 200 adet hisse 86.10 TL fiyattan satilmistir.
```

## 🎉 **Scenario 3: Corporate Actions Month (March 2025)**

### **Multiple Dividends & Capital Increases**
```
Mar 2, 2025: Degerli Musterimiz, CCOLA.E senedi %91.14 temettu vermis, hesaplariniza yansitilmistir.
Mar 5, 2025: Degerli Musterimiz, AEFES.E senedi %900 bedelsiz sermaye artirimi yapmis, hesaplariniza yansitilmistir
Mar 8, 2025: Degerli Musterimiz, TCELL.E senedi %154.55 temettu vermis, hesaplariniza yansitilmistir.
Mar 12, 2025: TCELL hissesinden 100 adet hisse 45.80 TL fiyattan alinmistir.
Mar 15, 2025: Degerli Musterimiz, TOASO.E senedi %50 bedelsiz sermaye artirimi yapmis, hesaplariniza yansitilmistir
Mar 18, 2025: Degerli Musterimiz, SISE.E senedi %67.25 temettu vermis, hesaplariniza yansitilmistir.
```

## 📈 **Scenario 4: Large Volume Trading (April 2025)**

### **High-Value Transactions**
```
Apr 2, 2025: Cash Deposit - 150,000 TL
Apr 5, 2025: THYAO hissesinden 1500 adet hisse 105.60 TL fiyattan alinmistir.
Apr 8, 2025: TUPRS hissesinden 800 adet hisse 298.75 TL fiyattan alinmistir.
Apr 10, 2025: BIMAS senedinden 200 adet 252.40 TL fiyat ile alim islemi gerceklestirilmistir.
Apr 15, 2025: CCOLA hissesinden 2000 adet hisse 88.90 TL fiyattan alinmistir.
Apr 18, 2025: KRVGD hissesinden 5000 adet hisse 14.20 TL fiyattan alinmistir.
```

### **Profit Taking**
```
Apr 22, 2025: TUPRS hissesinden 600 adet hisse 310.50 TL fiyattan satilmistir.
Apr 25, 2025: THYAO hissesinden 800 adet hisse 108.90 TL fiyattan satilmistir.
Apr 28, 2025: CCOLA hissesinden 1200 adet hisse 92.30 TL fiyattan satilmistir.
```

## 🔄 **Scenario 5: Fractional Shares & Edge Cases (May 2025)**

### **Fractional Trading**
```
May 3, 2025: SISE senedinden 37.5 adet 49.60 TL fiyat ile alim islemi gerceklestirilmistir.
May 7, 2025: BIMAS senedinden 12.25 adet 255.80 TL fiyat ile satis islemi gerceklestirilmistir.
May 10, 2025: AEFES hissesinden 67.75 adet hisse 128.40 TL fiyattan alinmistir.
```

### **Very Small & Very Large Amounts**
```
May 12, 2025: TCELL hissesinden 2 adet hisse 47.20 TL fiyattan alinmistir.
May 15, 2025: ISDMR senedinden 10000 adet 38.90 TL fiyat ile alim islemi gerceklestirilmistir.
May 18, 2025: Cash Withdrawal - 5,000 TL
May 20, 2025: AGHOL hissesinden 1 adet hisse 92.50 TL fiyattan satilmistir.
```

## 💰 **Scenario 6: Cash Management Testing (June 2025)**

### **Multiple Cash Operations**
```
Jun 2, 2025: Cash Deposit - 50,000 TL
Jun 5, 2025: Cash Withdrawal - 15,000 TL
Jun 8, 2025: Cash Deposit - 75,000 TL
Jun 10, 2025: TUPRS hissesinden 300 adet hisse 305.20 TL fiyattan alinmistir.
Jun 12, 2025: Cash Withdrawal - 25,000 TL
Jun 15, 2025: THYAO hissesinden 200 adet hisse 110.75 TL fiyattan alinmistir.
```

### **Insufficient Funds Testing**
```
Jun 18, 2025: Try to buy BIMAS hissesinden 1000 adet hisse 260.00 TL fiyattan
Jun 20, 2025: Cash Deposit - 100,000 TL
Jun 22, 2025: BIMAS senedinden 200 adet 258.50 TL fiyat ile alim islemi gerceklestirilmistir.
```

## 🎯 **Scenario 7: Performance Analytics Testing**

### **Portfolio Rebalancing for Analytics**
```
Different time periods to test analytics:
- 1 week performance
- 1 month performance  
- 3 month performance
- 6 month performance
- 1 year performance

Test with holdings across multiple sectors:
- Technology: TCELL
- Banking: THYAO
- Food & Beverage: CCOLA, AEFES
- Chemicals: TUPRS, SISE
- Steel: ISDMR
- Automotive: TOASO
- Others: BIMAS, KRVGD, AGHOL
```

## 🧪 **Edge Case Testing Scenarios**

### **Message Parsing Edge Cases**

#### **Buy/Sell Variations:**
```
1. TUPRS hissesinden 0.1 adet hisse 285.50 TL fiyattan alinmistir.
2. THYAO    hissesinden    500    adet hisse 98.75 TL fiyattan    satilmistir.
3. sise senedinden 150 adet 46.20 tl fiyat ile alim islemi gerceklestirilmistir.
4. CCOLA Hissesinden 200 ADET Hisse 82.40 TL Fiyattan ALINMISTIR.
5. BIMAS senedinden 999999 adet 1.01 TL fiyat ile satis islemi gerceklestirilmistir.
```

#### **Event Message Variations:**
```
1. degerli musterimiz, tcell.e senedi %154.55 temettu vermis, hesaplariniza yansitilmistir.
2. DEGERLI MUSTERIMIZ, AEFES.E SENEDI %900 BEDELSIZ SERMAYE ARTIRIMI YAPMIS, HESAPLARINIZA YANSITILMISTIR
3. Değerli Müşterimiz, CCOLA.E senedi %0.01 temettü vermiş, hesaplarınıza yansıtılmıştır.
4. Degerli Musterimiz, THYAO.E senedi %999.99 bedelsiz sermaye artirimi yapmis, hesaplariniza yansitilmistir
```

### **Data Import/Export Testing**

#### **CSV Import Test Data:**
```csv
date,type,symbol,quantity,price,note
2025-01-15,buy,TUPRS,100,280.50,Test import buy
2025-01-16,sell,THYAO,50,99.25,Test import sell
2025-01-17,deposit,,10000,1.0,Test cash deposit
2025-01-18,withdrawal,,2000,1.0,Test cash withdrawal
2025-01-19,dividend,CCOLA,0,500.75,Test dividend
```

#### **Excel Import Test Data:**
```
Various formats:
- Different date formats (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD)
- Different decimal separators (, vs .)
- Empty cells and missing data
- Special characters in notes
- Very long symbol names
```

## 🔬 **Performance Testing Scenarios**

### **Load Testing:**
```
1. Import 1000+ transactions at once
2. Calculate portfolio with 50+ different stocks
3. Generate analytics for 2+ years of data
4. Test with extreme values (millions of shares, very high prices)
5. Concurrent API requests (multiple users)
```

### **Memory Testing:**
```
1. Large portfolio timeline calculations
2. Sector analysis with many stocks
3. Risk metrics for extended periods
4. Export large datasets (Excel/CSV)
```

## 🎨 **UI/UX Testing Scenarios**

### **Responsive Design:**
```
1. Test on mobile devices (320px width)
2. Test on tablets (768px width)
3. Test on desktop (1920px width)
4. Test on ultra-wide displays (2560px width)
```

### **User Interaction:**
```
1. Long loading times (network delays)
2. Error states (server down, API failures)
3. Empty states (no transactions, no holdings)
4. Very long stock names and notes
5. Special characters in all input fields
```

## 📋 **Test Execution Checklist**

### **Before Testing:**
- [ ] Backup current database
- [ ] Ensure backend is running
- [ ] Verify all API endpoints are accessible
- [ ] Check frontend build is current

### **During Testing:**
- [ ] Monitor backend logs for errors
- [ ] Check browser console for JavaScript errors
- [ ] Verify database integrity after each scenario
- [ ] Test message parsing accuracy
- [ ] Validate calculation correctness

### **After Testing:**
- [ ] Generate portfolio analytics report
- [ ] Export data to verify integrity
- [ ] Test data import/export roundtrip
- [ ] Verify all features work as expected
- [ ] Document any issues found

## 🎯 **Expected Outcomes**

### **Portfolio Composition After All Scenarios:**
```
Expected holdings across multiple sectors:
- Technology stocks with dividends received
- Mixed buy/sell positions showing FIFO cost basis
- Capital increases properly reflected
- Cash balance from deposits/withdrawals
- Accurate profit/loss calculations
- Proper analytics across all time periods
```

### **Analytics Features to Verify:**
- [ ] Risk metrics calculation
- [ ] Sector diversification analysis  
- [ ] Portfolio timeline accuracy
- [ ] Dashboard metrics correctness
- [ ] Market comparison functionality
- [ ] Performance summary accuracy

This comprehensive test suite will ensure all features work correctly under various real-world scenarios and edge cases. 