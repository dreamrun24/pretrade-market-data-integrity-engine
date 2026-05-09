# References

1. Leys, C., Ley, C., Klein, O., Bernard, P., & Licata, L. (2013).
   Detecting outliers: Do not use standard deviation around the mean,
   use absolute deviation around the median.
   *Journal of Experimental Social Psychology*, 49(4), 764-766.
   **Why This Matters:** Direct scientific basis for using MAD over
   standard deviation in `outliers.py`. Proves that for non-normal
   distributions, MAD is the correct spread measure.

2. Hampel, F.R. (1974). The influence curve and its role in robust
   estimation. *Journal of the American Statistical Association*,
   69(346), 383-393.
   **Why This Matters:** Original paper establishing robust statistics.
   The 1.4826 scaling constant used in `compute_mad()` comes from this
   work.

3. Cont, R. (2001). Empirical properties of asset returns: stylized
   facts and statistical issues. *Quantitative Finance*, 1(2), 223-236.
   **Why This Matters:** Canonical proof that financial returns have fat
   tails. The excess kurtosis values shown in the multi-ticker comparison
   chart directly replicate findings from this paper.

4. Elton, E.J., Gruber, M.J., & Blake, C.R. (1996). Survivorship bias
   and mutual fund performance. *The Review of Financial Studies*,
   9(4), 1097-1120.
   **Why This Matters:** Quantifies survivorship bias at ~0.9% per year.
   Explains why `gaps.py` records *why* data stops, not just that it
   stops - absence of a stock is itself data.

5. Lo, A.W. & MacKinlay, A.C. (1990). Data-snooping biases in tests of
   financial asset pricing models. *The Review of Financial Studies*,
   3(3), 431-467.
   **Why This Matters:** Foundation for understanding look-ahead bias.
   Explains why `gaps.py` uses forward-fill (not interpolation) -
   interpolation uses future prices unavailable at the time.

6. CRSP Data Description Guide. Center for Research in Security Prices,
   University of Chicago.
   **Why This Matters:** Institutional standard for adjustment factors,
   delisting handling, and point-in-time data. The split and dividend
   adjustment logic in `corporate_actions.py` follows CRSP conventions.

7. Lopez de Prado, M. (2018). *Advances in Financial Machine Learning*.
   Wiley. Chapters 2-3.
   **Why This Matters:** Chapters 2-3 cover financial data structures
   and quality for ML. The pipeline architecture (validate -> adjust ->
   fill -> detect -> score) aligns with the data bar framework described
   here.
