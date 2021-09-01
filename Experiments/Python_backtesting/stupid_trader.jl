

function rand_dec()
    rand_num = rand()

    if rand_num < 0.01
        return "buy"
    elseif rand_num > 0.99
        return "sell"
    else
        return "idle"
    end

end



