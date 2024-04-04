[ pos, time ] = ChrisJIMtraj( 3 );
if length(pos) >= 5000 && length(time) >= 5000
    position = pos(1:5000);
    time = time(1:5000);
end

plot(time,pos)