<?php
set_include_path(get_include_path() . PATH_SEPARATOR . dirname(__FILE__) . DIRECTORY_SEPARATOR . 'libpy2php');
require_once ('libpy2php.php');
require_once ('random.php');
function everynth($array, $n) {
	$result = array();
    $i = -1;
    foreach($array as $key => $value) {
	    if ($i++ == $n) {
            $i = 0;
	    }
        if($i == 0) {
       	    $result[$key] = $value;
        }
    }
    return $result;
}
function primesbelow($N) {
    $correction = (($N % 6) > 1);
    $N = [0 => $N, 1 => ($N - 1), 2 => ($N + 4), 3 => ($N + 3), 4 => ($N + 2), 5 => ($N + 1) ][($N % 6) ];
    $sieve = ([true] * ($N / 3));
    $sieve[0] = false;
    foreach (pyjslib_range(((pyjslib_int(pow($N, 0.5)) / 3) + 1)) as $i) {
        if ($sieve[$i]) {
            $k = ((3 * $i) + 1) | 1;
            everynth(array_splice($sieve, floor($k*$k / 3)), 2*$k) = ([false] * ((((($N / 6) - (($k * $k) / 6)) - 1) / $k) + 1));
            everynth(array_splice($sieve, floor((k*k + 4*k - 2*k*(i%2)) / 3)), 2*$k) = ([false] * ((((($N / 6) - (((($k * $k) + (4 * $k)) - ((2 * $k) * ($i % 2))) / 6)) - 1) / $k) + 1));
        }
    }
    return ([2, 3] + array_map(function ($i, $sieve) { if($sieve[$i]) return (3 * $i + 1) | 1; }, pyjslib_range(1, (($N / 3) - $correction)), $sieve));
    
}
$smallprimeset = set(primesbelow(100000));
$_smallprimeset = 100000;
function isprime($n, $precision = 7) {
    if (($n == 1) || (($n % 2) == 0)) {
        return false;
    } else if (($n < 1)) {
        throw new $ValueError('Out of bounds, first argument must be > 0');
    } else if (($n < $_smallprimeset)) {
        return in_array($n, $smallprimeset);
    }
    $d = ($n - 1);
    $s = 0;
    while ((($d % 2) == 0)) {
        $d
        //= 2;
        $s+= 1;
    }
    foreach (pyjslib_range($precision) as $repeat) {
        $a = random::randrange(2, ($n - 2));
        $x = pow($a, $d, $n);
        if (($x == 1) || ($x == ($n - 1))) {
            continue;
        }
        foreach (pyjslib_range(($s - 1)) as $r) {
            $x = pow($x, 2, $n);
            if (($x == 1)) {
                return false;
            }
            if (($x == ($n - 1))) {
                break;
            }
        }
    }
    return true;
}
function pollard_brent($n) {
    if ((($n % 2) == 0)) {
        return 2;
    }
    if ((($n % 3) == 0)) {
        return 3;
    }
    list($y, $c, $m) = [random::randint(1, ($n - 1)), random::randint(1, ($n - 1)), random::randint(1, ($n - 1)) ];
    list($g, $r, $q) = [1, 1, 1];
    while (($g == 1)) {
        $x = $y;
        foreach (pyjslib_range($r) as $i) {
            $y = ((pow($y, 2, $n) + $c) % $n);
        }
        $k = 0;
        while (($k < $r) && ($g == 1)) {
            $ys = $y;
            foreach (pyjslib_range(min($m, ($r - $k))) as $i) {
                $y = ((pow($y, 2, $n) + $c) % $n);
                $q = (($q * abs(($x - $y))) % $n);
            }
            $g = gcd($q, $n);
            $k+= $m;
        }
        $r*= 2;
    }
    if (($g == $n)) {
        while (true) {
            $ys = ((pow($ys, 2, $n) + $c) % $n);
            $g = gcd(abs(($x - $ys)), $n);
            if (($g > 1)) {
                break;
            }
        }
    }
    return $g;
}
$smallprimes = primesbelow(10000);
function primefactors($n, $sort = false) {
    $factors = [];
    $limit = (pyjslib_int(pow($n, 0.5)) + 1);
    foreach ($smallprimes as $checker) {
        if (($checker > $limit)) {
            break;
        }
        while ((($n % $checker) == 0)) {
            $factors[] = $checker;
            $n
            //= $checker;
            $limit = (pyjslib_int(pow($n, 0.5)) + 1);
            if (($checker > $limit)) {
                break;
            }
        }
    }
    if (($n < 2)) {
        return $factors;
    }
    while (($n > 1)) {
        if (isprime($n)) {
            $factors[] = $n;
            break;
        }
        $factor = pollard_brent($n);
        $factors->extend(primefactors($factor));
        $n
        //= $factor;
        
    }
    if ($sort) {
        $factors->sort();
    }
    return $factors;
}
function factorization($n) {
    $factors = [];
    foreach (primefactors($n) as $p1) {
        try {
            $factors[$p1]+= 1;
        }
        catch(KeyError $e) {
            $factors[$p1] = 1;
        }
    }
    return $factors;
}
$totients = [];
function totient($n) {
    if (($n == 0)) {
        return 1;
    }
    try {
        return $totients[$n];
    }
    catch(KeyError $e) {
    }
    $tot = 1;
    foreach (factorization($n)->items() as list($p, $exp)) {
        $tot*= (($p - 1) * pow($p, ($exp - 1)));
    }
    $totients[$n] = $tot;
    return $tot;
}
function gcd($a, $b) {
    if (($a == $b)) {
        return $a;
    }
    while (($b > 0)) {
        list($a, $b) = [$b, ($a % $b) ];
    }
    return $a;
}
function lcm($a, $b) {
    return (abs(($a * $b)) / gcd($a, $b));
}
